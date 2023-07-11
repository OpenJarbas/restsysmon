try:
    import screen_brightness_control as sbc
except:
    sbc = None


def get_sbc_routes(app):
    # Screen
    @app.route("/brightness")
    def get_brightness():
        # get the brightness
        brightness = sbc.get_brightness()
        return str(brightness[0])

    @app.route("/monitor/<monitor>/brightness")
    def monitor_brightness(monitor):
        # get the brightness for the primary monitor
        primary = sbc.get_brightness(display=monitor)
        return str(primary)

    # TODO - for now this repo should be read-only
    #  reconsider after adding auth
    # @app.route("/monitor/<monitor>/set_brightness/<value>")
    def set_monitor_brightness(monitor, value):
        # set the brightness to 100% for the primary monitor
        sbc.set_brightness(value, display=monitor)
        return f"{monitor} - {value} %"

    # TODO - for now this repo should be read-only
    #  reconsider after adding auth
    # @app.route("/set_brightness/<value>")
    def set_brightness(value):
        # set the brightness to 100%
        sbc.set_brightness(value, display=0)
        return str(value)

    @app.route("/monitors")
    def list_monitors():
        # show the current brightness for each detected monitor
        return sbc.list_monitors()

    return app
