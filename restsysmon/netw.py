import urllib

import psutil


def get_netw_routes(app):
    # network
    @app.route("/network_interfaces")
    def network():
        return list(psutil.net_if_addrs().keys())

    @app.route("/network/<interface>")
    def network_ip(interface):
        ifs = psutil.net_if_addrs()
        if interface in ifs:
            return ifs[interface][0].address
        return ""

    @app.route("/external_ip")
    def external_ip():
        return urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')

    return app
