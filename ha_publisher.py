import json
import string
from threading import Lock

import requests
import time
from zeroconf import ServiceBrowser, ServiceStateChange
from zeroconf import Zeroconf

IDENTIFIER = "restsysmon"
HA_URL = "http://192.168.1.8:8123"
HA_TOKEN = "..."


class HASensorPusher:
    def __init__(self, identifier=IDENTIFIER):
        self.zero = None
        self.browser = None
        self.nodes = {}
        self.running = False
        self.identifier = identifier.encode("utf-8")
        self.ttl = 10  # seconds between rounds of sensor readings
        self.sleep_time = 0.3  # seconds between individual sensor readings
        self.lock = Lock()

    @staticmethod
    def ha_binary_sensor_update(device_id, state="on", attrs=None):
        device_id = device_id.replace(" ", "_")
        for s in string.punctuation:
            device_id = device_id.replace(s, "_")
        attrs = attrs or {"friendly_name": device_id,
                          "state_color": True,
                          "device_class": "presence"}

        print("updating binary sensor - ", device_id)
        response = requests.post(
            f"{HA_URL}/api/states/binary_sensor.{IDENTIFIER}_{device_id}",
            headers={
                "Authorization": f"Bearer {HA_TOKEN}",
                "content-type": "application/json",
            },
            data=json.dumps({"state": state, "attributes": attrs}),
        )
        print(response.text)

    @staticmethod
    def ha_sensor_update(device_id, state="on", attrs=None):
        attrs = attrs or {"friendly_name": device_id,
                          "state_color": True}
        print("updating sensor - ", device_id)
        response = requests.post(
            f"{HA_URL}/api/states/sensor.{IDENTIFIER}_{device_id}",
            headers={
                "Authorization": f"Bearer {HA_TOKEN}",
                "content-type": "application/json",
            },
            data=json.dumps({"state": state, "attributes": attrs}),
        )
        print(response.text)

    def on_new_node(self, node):
        device_id = node["name"]
        print("found", node)
        self.on_node_update(node)
        self.get_readings()
        self.get_info(device_id)  # one time sensor readings

    def on_lost_node(self, node):
        print("lost", node)
        self.on_node_update(node)

    def on_node_update(self, node):
        device_id = node["name"]
        self.nodes[device_id] = node
        self.ha_binary_sensor_update(device_id, state=node["state"],
                                     attrs={"friendly_name": node["name"],
                                            "state_color": True,
                                            "device_class": "presence"})

    def on_service_state_change(self, zeroconf, service_type, name,
                                state_change):
        info = zeroconf.get_service_info(service_type, name)
        if info and info.properties:
            for key, value in info.properties.items():
                if key == b"type" and value == self.identifier:
                    host = info._properties[b"host"].decode("utf-8")
                    port = info._properties[b"port"].decode("utf-8")
                    name = info._properties[b"name"].decode("utf-8")
                    node = {"host": host, "port": port, "name": name}
                    node["last_seen"] = time.time()
                    if state_change is ServiceStateChange.Added:
                        node["state"] = "on"
                        self.on_new_node(node)
                    elif ServiceStateChange.Removed:
                        node["state"] = "off"
                        self.on_lost_node(node)
                    else:
                        node["state"] = "on"
                        self.on_node_update(node)

    def start(self):
        self.zero = Zeroconf()
        self.browser = ServiceBrowser(self.zero, "_http._tcp.local.",
                                      handlers=[self.on_service_state_change])
        self.running = True
        while self.running:
            try:
                self.get_readings()
                time.sleep(self.ttl)
            except KeyboardInterrupt:
                break
        self.stop()

    def stop(self):
        if self.zero:
            self.zero.close()
        self.zero = None
        self.browser = None
        self.running = False

    def get_info(self, device_id):
        data = self.nodes[device_id]
        url = f"{data['host']}:{data['port']}"
        readings = {
            "os": f"{url}/os_name",
            "boot_time": f"{url}/boot_time",
            "system": f"{url}/system",
            "release": f"{url}/release",
            "machine": f"{url}/machine",
            "architecture": f"{url}/architecture",
            "cpu_count": f"{url}/cpu_count",
            "fans": f"{url}/fans",
            "network_interfaces": f"{url}/network_interfaces",
            "external_ip": f"{url}/external_ip",
            "procs": f"{url}/procs",
            "is_systemd": f"{url}/is_systemd",
            "is_dbus": f"{url}/is_dbus"
        }
        for sensor_name, url in readings.items():
            self.read_sensor(device_id, sensor_name, url)
            time.sleep(self.sleep_time)

    def read_sensor(self, device_id, sensor_name, url):
        sensor_id = f"{device_id}_{sensor_name}"
        try:
            res = requests.get("http://" + url)
            try:
                res = res.json()
            except:
                res = res.text
            try:  # numeric
                if "/is_" in url:
                    res = str(res) == "1"
                    self.ha_binary_sensor_update(sensor_id, state="on" if res else "off",
                                                 attrs={"friendly_name": sensor_name,
                                                        "state_color": True,
                                                        "device_class": "presence"})
                elif url.endswith("_count"):
                    res = int(res)
                    a = {"friendly_name": sensor_name,
                         "state_color": True}
                    self.ha_sensor_update(sensor_id, state=str(res), attrs=a)
                else:
                    res = float(res)  # numeric reading
                    a = {"friendly_name": sensor_name,
                         "state_color": True}
                    if "temperature" in url:
                        a["unit_of_measurement"] = "°C"
                    self.ha_sensor_update(sensor_id, state=str(res), attrs=a)

            except Exception as e:
                # text
                if isinstance(res, list):
                    if sensor_id.endswith("pulseaudio_list_cards"):
                        for e in res:
                            sensor_id = f"{device_id}_pulseaudio_card_{e['index']}"
                            f = e.get("card_name") or e.get("name") or sensor_id
                            self.ha_binary_sensor_update(sensor_id, state="on",
                                                         attrs={"friendly_name": f.lower().strip(),
                                                                "state_color": True,
                                                                "device_class": "presence"})
                    elif sensor_id.endswith("pulseaudio_list_sources"):
                        for e in res:
                            sensor_id = f"{device_id}_pulseaudio_source_{e['index']}"
                            self.ha_binary_sensor_update(sensor_id, state="on",
                                                         attrs={"friendly_name": e.get("name") or sensor_id,
                                                                "state_color": True,
                                                                "device_class": "presence"})
                    elif sensor_id.endswith("pulseaudio_list_sinks"):
                        for e in res:
                            sensor_id = f"{device_id}_pulseaudio_sink_{e['index']}"
                            self.ha_binary_sensor_update(sensor_id, state="on",
                                                         attrs={"friendly_name": e.get("name") or sensor_id,
                                                                "state_color": True,
                                                                "device_class": "presence"})
                    elif sensor_id.endswith("pulseaudio_list_input_sinks"):
                        # streams of interest, even if not currently playing will report a status
                        APPS = [
                            "netflix",
                            "spotify"
                        ]
                        for app in APPS:

                            if any(app == _["application"] for _ in res):
                                # app names handled below, we just want streams here
                                # eg, detect netflix in firefox via pulseaudio playback
                                continue

                            if any(app == _.get('media_name', "").lower() for _ in res):
                                # detected application running via pulseaudio playback
                                state = "on"
                                mute_state = "off"  # TODO - check the playback info
                            else:
                                state = mute_state = "off"

                            sensor_id = f"{device_id}_pulseaudio_stream_{app}"
                            self.ha_binary_sensor_update(sensor_id, state=state,
                                                         attrs={"friendly_name": app,
                                                                "state_color": True,
                                                                "device_class": "presence"})
                            sensor_id = f"{device_id}_pulseaudio_stream_{app}_muted"
                            self.ha_binary_sensor_update(sensor_id, state=mute_state,
                                                         attrs={"friendly_name": app + " muted",
                                                                "state_color": True,
                                                                "device_class": "presence"})

                        for e in res:
                            sensor_id = f"{device_id}_pulseaudio_stream_{e['application']}"
                            f = e.get('media_name') or e.get('name') or e.get('application')
                            self.ha_binary_sensor_update(sensor_id, state="on" if e.get("playing") else "off",
                                                         attrs={"friendly_name": f.lower().strip(),
                                                                "state_color": True,
                                                                "device_class": "presence"})

                            sensor_id = f"{device_id}_pulseaudio_stream_{e['application']}_muted"
                            f = e.get('media_name') or e.get('name') or e.get('application')
                            self.ha_binary_sensor_update(sensor_id, state="on" if e.get("mute") else "off",
                                                         attrs={"friendly_name": f.lower().strip() + " muted",
                                                                "state_color": True,
                                                                "device_class": "presence"})

                            sensor_id = f"{device_id}_pulseaudio_stream_{e['application']}_sink"
                            f = e.get('media_name') or e.get('name') or e.get('application')
                            self.ha_sensor_update(sensor_id, state=str(e["sink"]),
                                                  attrs={"friendly_name": f.lower().strip() + " sink",
                                                         "state_color": True,
                                                         "device_class": "presence"})
                    elif sensor_id.endswith("network_interfaces"):
                        for e in res:
                            sensor_id = f"{device_id}_network_if_{e}"
                            self.ha_binary_sensor_update(sensor_id, state="on",
                                                         attrs={"friendly_name": e,
                                                                "state_color": True,
                                                                "device_class": "presence"})
                    else:
                        print("## TODO", sensor_id, res)
                    pass
                elif isinstance(res, dict):
                    # print("## TODO", sensor_id, res)
                    pass
                else:
                    a = {"friendly_name": sensor_name,
                         "state_color": True}
                    self.ha_sensor_update(sensor_id, state=str(res), attrs=a)
        except:
            raise

    def get_readings(self):
        with self.lock:
            for device_id, data in dict(self.nodes).items():
                if data["state"] == "on":
                    url = f"{data['host']}:{data['port']}"
                    readings = {
                        "cpu_usage": f"{url}/cpu_usage",
                        "cpu_freq": f"{url}/cpu_freq",
                        "cpu_freq_max": f"{url}/cpu_freq_max",
                        "cpu_freq_min": f"{url}/cpu_freq_min",
                        "cpu_temperature": f"{url}/cpu_temperature",
                        "memory_usage": f"{url}/memory_usage",
                        "memory_total": f"{url}/memory_total",
                        "swap_usage": f"{url}/swap_usage",
                        "swap_total": f"{url}/swap_total",
                        "disk_usage": f"{url}/disk_usage",
                        "disk_percent": f"{url}/disk_percent",
                        "disk_total": f"{url}/disk_total",
                        "battery_percent": f"{url}/battery_percent",
                        "external_ip": f"{url}/external_ip",
                        "is_kdeconnect": f"{url}/is_kdeconnect",
                        "is_pulseaudio": f"{url}/is_pulseaudio",
                        "is_pipewire": f"{url}/is_pipewire",
                        "is_plasma": f"{url}/is_plasma",
                        "is_hivemind": f"{url}/is_hivemind",
                        "is_ovos": f"{url}/is_ovos",
                        "is_spotify": f"{url}/is_spotify",
                        "is_firefox": f"{url}/is_firefox",
                        #   "pulseaudio_info": f"{url}/pulseaudio/info",
                        "pulseaudio_version": f"{url}/pulseaudio/version",
                        "pulseaudio_channel_count": f"{url}/pulseaudio/channel_count",
                        "pulseaudio_default_sink": f"{url}/pulseaudio/default_sink",
                        "pulseaudio_default_source": f"{url}/pulseaudio/default_source",
                        "pulseaudio_hostname": f"{url}/pulseaudio/hostname",
                        "pulseaudio_now_playing": f"{url}/pulseaudio/now_playing",
                        "pulseaudio_list_cards": f"{url}/pulseaudio/list_cards",
                        "pulseaudio_list_sources": f"{url}/pulseaudio/list_sources",
                        "pulseaudio_list_sinks": f"{url}/pulseaudio/list_sinks",
                        "pulseaudio_list_input_sinks": f"{url}/pulseaudio/list_input_sinks",
                        "pulseaudio_is_playing": f"{url}/pulseaudio/is_playing",
                        "pulseaudio_bluez_active": f"{url}/pulseaudio/is_bluez_active",
                        "pulseaudio_bluez_connected": f"{url}/pulseaudio/is_bluez_connected",
                        "brightness": f"{url}/brightness"
                    }
                    for sensor_name, url in readings.items():
                        self.read_sensor(device_id, sensor_name, url)
                        time.sleep(self.sleep_time)


if __name__ == "__main__":
    ha = HASensorPusher()
    ha.start()
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
    ha.stop()
