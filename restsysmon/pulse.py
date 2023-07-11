try:
    import pulsectl

    pulse = pulsectl.Pulse('restsysmon')
except:
    pulse = None


def get_pa_routes(app):
    # Pulseaudio
    @app.route("/pulseaudio/info")
    def pa_info():
        info = pulse.server_info().__dict__
        info.pop("c_struct_fields")
        return info

    @app.route("/pulseaudio/version")
    def pa_version():
        return pulse.server_info().server_version

    @app.route("/pulseaudio/channel_count")
    def pa_channel_count():
        return str(pulse.server_info().channel_count)

    @app.route("/pulseaudio/default_sink")
    def pa_sink():
        return pulse.server_info().default_sink_name

    @app.route("/pulseaudio/default_source")
    def pa_source():
        return pulse.server_info().default_source_name

    @app.route("/pulseaudio/hostname")
    def pa_hostname():
        return pulse.server_info().host_name

    @app.route("/pulseaudio/list_cards")
    def pa_list_cards():
        sinks = []

        for s in pulse.card_list():
            sinks.append({
                "index": s.index,
                "profile": s.profile_active.name,
                "name": s.name,
                "card_name": s.proplist.get("alsa.card_name") or s.name,
                "description": s.proplist.get("device.description", ""),
                "form_factor": s.proplist.get("device.form_factor", "unknown")
            })
        return sinks

    @app.route("/pulseaudio/list_sources")
    def pa_list_sources():
        sinks = []

        for s in pulse.source_list():
            volumes = [v * 100 for v in s.volume.__dict__["values"]]

            sinks.append({
                "index": s.index,
                "mute": s.mute,
                "name": s.name,
                "card": s.card,
                "channel_count": s.channel_count,
                "channel_list": s.channel_list,
                "driver": s.driver,
                "description": s.description,
                "state": str(s.state).split("state=")[-1][:-1],
                "volumes": volumes
            })
        return sinks

    @app.route("/pulseaudio/list_sinks")
    def pa_list_sinks():
        sinks = []

        for s in pulse.sink_list():
            volumes = [v * 100 for v in s.volume.__dict__["values"]]

            sinks.append({
                "index": s.index,
                "mute": s.mute,
                "name": s.name,
                "card": s.card,
                "channel_count": s.channel_count,
                "channel_list": s.channel_list,
                "driver": s.driver,
                "description": s.description,
                "state": str(s.state).split("state=")[-1][:-1],
                "volumes": volumes
            })
        return sinks

    @app.route("/pulseaudio/list_input_sinks")
    def pa_list_input_sinks():
        sinks = []
        for s in pulse.sink_input_list():
            volumes = [v * 100 for v in s.volume.__dict__["values"]]
            sinks.append({
                "index": s.index,
                "mute": s.mute,
                "name": s.name,
                "playing": 1 if not s.corked else 0,
                "media_name": s.proplist.get("media.name") or "",
                "application": s.proplist.get('application.name') or
                               s.proplist.get('application.binary') or
                               s.proplist.get('application.icon_name') or "",
                "sink": s.sink,
                "channel_count": s.channel_count,
                "channel_list": s.channel_list,
                "driver": s.driver,
                "volumes": volumes
            })
        return sinks

    @app.route("/pulseaudio/is_playing")
    def pa_is_playing():
        if any(not s.corked for s in pulse.sink_input_list()):
            return "1"
        return "0"

    @app.route("/pulseaudio/now_playing")
    def pa_now_playing():
        now_playing_str = ""
        for s in pulse.sink_input_list():
            if not s.corked:
                now_playing_str += s.name + "\n"
        return now_playing_str.strip()

    return app
