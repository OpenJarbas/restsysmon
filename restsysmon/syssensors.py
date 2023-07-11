import os
import platform
import shutil

import psutil


def get_sensor_routes(app):
    # system info
    @app.route("/os_name")
    def os_name():
        return os.name

    @app.route("/boot_time")
    def boot_time():
        return str(psutil.boot_time())

    @app.route("/system")
    def system():
        return platform.system()

    @app.route("/release")
    def release():
        return platform.release()

    @app.route("/machine")
    def machine():
        return platform.machine()

    @app.route("/architecture")
    def architecture():
        return str(platform.architecture()[0])

    # sensors
    @app.route("/cpu_count")
    def cpu_count():
        return str(os.cpu_count())

    @app.route("/cpu_usage")
    def cpu_usage():
        return str(psutil.cpu_percent(1))

    @app.route("/cpu_freq")
    def cpu_freq():
        return str(psutil.cpu_freq().current)

    @app.route("/cpu_freq_max")
    def cpu_freq_max():
        return str(psutil.cpu_freq().max)

    @app.route("/cpu_freq_min")
    def cpu_freq_min():
        return str(psutil.cpu_freq().min)

    @app.route("/cpu_temperature")
    def cpu_temperature():
        return str(psutil.sensors_temperatures()['coretemp'][0].current)

    @app.route("/memory_usage")
    def memory_usage():
        return str(psutil.virtual_memory()[2])

    @app.route("/memory_total")
    def memory_total():
        return str(psutil.virtual_memory()[0])

    @app.route("/swap_usage")
    def swap_usage():
        return str(psutil.swap_memory()[3])

    @app.route("/swap_total")
    def swap_total():
        return str(psutil.swap_memory()[0])

    @app.route("/disk_usage")
    def disk_usage():
        total, used, free = shutil.disk_usage("/")
        return str(used)

    @app.route("/disk_percent")
    def disk_percent():
        total, used, free = shutil.disk_usage("/")
        return str(used * 100 / total)

    @app.route("/disk_total")
    def disk_total():
        total, used, free = shutil.disk_usage("/")
        return str(total)

    @app.route("/battery_percent")
    def battery_percent():
        battery = psutil.sensors_battery()
        return str(battery.percent)

    @app.route("/fans")
    def fans():
        return {label: [f.label for f in fans]
                for label, fans in psutil.sensors_fans().items()}

    @app.route("/fan/<label>/<fan_name>")
    def get_fan(label, fan_name):
        fans = psutil.sensors_fans().items()
        if label in fans:
            for f in fans[label]:
                if f.label == fan_name:
                    return str(f.current)
        return "0"

    return app
