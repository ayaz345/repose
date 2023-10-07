from urllib.parse import urlparse
from argparse import ArgumentTypeError

from .target import Target


class HostParseError(ValueError, ArgumentTypeError):
    # Note: need to inherit ArgumentTypeError so the custom exception
    # messages get shown to the users properly
    # by L{argparse.ArgumentParser._get_value}

    def __init__(self, message):
        super(HostParseError, self).__init__(f"Target host: {message}")


class PortNotIntError(HostParseError):
    def __init__(self, hostname):
        super(PortNotIntError, self).__init__(
            f"Wrong port specification on Host: {hostname}"
        )


class ParseHosts(dict):
    def __init__(self, arg):
        """
        arg is string with hosts in socket format username@host:port
        """
        x = urlparse(f"//{arg}")
        try:
            if x.port:
                keyname = f"{x.hostname}:{x.port}"
                port = x.port
            else:
                keyname = x.hostname
                port = 22

            username = x.username if x.username else "root"

            host = [(keyname, Target(x.hostname, port, username))]
        except ValueError:
            raise PortNotIntError(x.hostname)
        super(ParseHosts, self).__init__(host)
