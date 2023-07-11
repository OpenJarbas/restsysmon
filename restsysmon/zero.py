IDENTIFIER = "restsysmon"


def setup_zeroconf(NAME, PORT):
    try:
        # if zero conf is installed, enable auto discovery

        from zeroconf import NonUniqueNameException
        from zeroconf import Zeroconf, ServiceInfo
        import ipaddress
        import socket

        def _get_ip():
            # taken from https://stackoverflow.com/a/28950776/13703283
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # doesn't even have to be reachable
                s.connect(('10.255.255.255', 1))
                IP = s.getsockname()[0]
            except Exception:
                IP = '127.0.0.1'
            finally:
                s.close()
            return IP

        class ZeroConfAnnounce:
            IP = _get_ip()
            zero = Zeroconf()
            info = ServiceInfo(
                "_http._tcp.local.",
                f" - {NAME}._http._tcp.local.",
                addresses=[ipaddress.ip_address(IP).packed],
                port=PORT,
                properties={"type": IDENTIFIER,
                            "name": NAME,
                            "host": IP,
                            "port": PORT},
            )
            try:
                zero.register_service(info)
                print(f"Announcing node via Zeroconf")
            except NonUniqueNameException:  # TODO - why is this being called twice ???
                pass

            @classmethod
            def shutdown(cls):
                if cls.zero:
                    cls.zero.unregister_service(cls.info)
                    cls.zero.close()
                cls.zero = None
    except:
        # no auto discovery
        ZeroConfAnnounce = None

    return ZeroConfAnnounce
