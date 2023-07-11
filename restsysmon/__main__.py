import subprocess

from flask import Flask

from restsysmon.zero import setup_zeroconf

# TODO - from argparse
DEVELOPMENT_ENV = False
PORT = 5000
NAME = "AsusTUF"


def get_app():
    from restsysmon.pulse import get_pa_routes
    from restsysmon.screen import get_sbc_routes
    from restsysmon.syssensors import get_sensor_routes
    from restsysmon.procs import get_procs_routes
    from restsysmon.netw import get_netw_routes

    # TODO - check os and decide what routes to load
    # want to support Windows and MacOS too
    app = Flask(__name__)
    app = get_pa_routes(app)
    app = get_sbc_routes(app)
    app = get_sensor_routes(app)
    app = get_procs_routes(app)
    app = get_netw_routes(app)

    @app.route("/")
    def index():
        return NAME

    # notify platform
    # TODO - for now this repo should be read-only
    #  reconsider after adding auth
    # @app.route("/notify/<message>")
    def notify(message):
        subprocess.call(['notify-send', message])
        return message

    return app


if __name__ == "__main__":

    zero = setup_zeroconf(NAME, PORT)

    app = get_app()
    app.run(debug=DEVELOPMENT_ENV, host="0.0.0.0", port=PORT)

    if zero is not None:
        zero.shutdown()
