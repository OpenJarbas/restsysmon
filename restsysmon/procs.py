import getpass
import os
import signal

import psutil


def get_procs_routes(app):
    # running processes
    @app.route("/procs")
    def process():
        return {p.pid: p.info['name']
                for p in psutil.process_iter(['name', 'username'])
                if p.info['username'] == getpass.getuser()}

    def _find_proc(name):
        for p in psutil.process_iter(["name", "exe", "cmdline"]):
            if name == p.info['name'] or \
                    p.info['exe'] and os.path.basename(p.info['exe']) == name or \
                    p.info['cmdline'] and p.info['cmdline'][0] == name:
                return p

    @app.route("/get_process/<name>")
    def get_process(name):
        p = _find_proc(name)
        if p:
            return {"pid": str(p.pid),
                    "status": p.status().upper(),
                    "name": p.name(),
                    "exe": p.info["exe"],
                    "cmdline": " ".join(p.info["cmdline"])}
        return {}

    @app.route(f"/process_status/<name>")
    def process_status(name):
        p = _find_proc(name)
        if p:
            return p.status().upper()
        return "not running".upper()

    # TODO - for now this repo should be read-only
    #  reconsider after adding auth
    # @app.route("/process_kill/<pid>")
    def process_kill(pid):
        include_parent = True
        sig = signal.SIGTERM
        timeout = None

        try:
            assert pid != os.getpid(), "won't kill myself"
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            if include_parent:
                children.append(parent)
            for p in children:
                try:
                    p.send_signal(sig)
                except psutil.NoSuchProcess:
                    pass
            gone, alive = psutil.wait_procs(children, timeout=timeout,
                                            callback=None)
            return str(gone)
        except Exception as e:
            return "0"

    # processes of interest indicating system capabilities
    @app.route("/is_systemd")
    def is_systemd():
        p = _find_proc("systemd")
        if p:
            return "1"
        return "0"

    @app.route("/is_dbus")
    def is_dbus():
        p = _find_proc("dbus-daemon")
        if p:
            return "1"
        return "0"

    @app.route("/is_kdeconnect")
    def is_kdeconnect():
        p = _find_proc("kdeconnectd")
        if p:
            return "1"
        return "0"

    @app.route("/is_pulseaudio")
    def is_pulseaudio():
        p = _find_proc("pulseaudio")
        if p:
            return "1"
        return "0"

    @app.route("/is_pipewire")
    def is_pipewire():
        p = _find_proc("pipewire")
        if p:
            return "1"
        return "0"

    @app.route("/is_plasma")
    def is_plasma():
        p = _find_proc("plasmashell")
        if p:
            return "1"
        return "0"

    @app.route("/is_hivemind")
    def is_hivemind():
        p = _find_proc("hivemind-core")
        if p:
            return "1"
        return "0"

    @app.route("/is_ovos")
    def is_ovos():
        p = _find_proc("ovos-core")
        if p:
            return "1"
        return "0"

    @app.route("/is_spotify")
    def is_spotify():
        # TODO - raspotify / spotifyd etc
        p = _find_proc("spotify")
        if p:
            return "1"
        return "0"

    @app.route("/is_firefox")
    def is_firefox():
        # TODO - other browsers
        p = _find_proc("firefox")
        if p:
            return "1"
        return "0"

    @app.route("/is_minidlna")
    def is_minidlna():
        p = _find_proc("minidlna")
        if p:
            return "1"
        return "0"

    @app.route("/is_upmpdcli")
    def is_upmpdcli():
        p = _find_proc("upmpdcli")
        if p:
            return "1"
        return "0"

    return app
