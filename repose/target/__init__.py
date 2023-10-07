from logging import getLogger
from ..utils import timestamp

from ..connection import Connection, CommandTimeout
from .parsers.product import parse_system
from .parsers.repository import parse_repositories
from ..messages import ConnectingTargetFailedMessage
from ..types.repositories import Repositories

logger = getLogger("repose.target")


class Target(object):
    def __init__(self, hostname, port, username, connector=Connection):
        # TODO: timeout handling ?
        self.port = port
        self.hostname = hostname
        self.username = username
        self.products = None
        self.raw_repos = None
        self.repos = None
        self.connector = connector
        self.is_connected = False
        self.connection = self.connector(self.hostname, self.username, self.port)
        self.out = []

    def __repr__(self):
        return f"<{self.__class__.__name__} object {self.username}@{self.hostname}:{self.port} - connected: {self.is_connected}>"

    def connect(self):
        if not self.is_connected:
            logger.info(f"Connecting to {self.hostname}:{self.port}")
            try:
                self.connection.connect()
            except BaseException as e:
                logger.critical(
                    ConnectingTargetFailedMessage(self.hostname, self.port, e)
                )
            else:
                self.is_connected = True

        return self

    def read_products(self):
        if not self.is_connected:
            self.connect()
        self.products = parse_system(self.connection)

    def close(self):
        self.connection.close()
        self.is_connected = False

    def __bool__(self):
        return self.is_connected

    def run(self, command, lock=None):
        logger.debug(f"run {command} on {self.hostname}:{self.port}")
        time_before = timestamp()

        try:
            stdout, stderr, exitcode = self.connection.run(command, lock)
        except CommandTimeout:
            logger.critical(f'{self.hostname}: command "{command}" timed out')
            exitcode = -1
        except AssertionError:
            logger.debug("zombie command terminated", exc_info=True)
            return
        except Exception as e:
            # failed to run command
            logger.error(f'{self.hostname}: failed to run command "{command}"')
            logger.debug(f"exception {e}", exc_info=True)
            exitcode = -1

        runtime = int(timestamp()) - int(time_before)

        self.out.append([command, stdout, stderr, exitcode, runtime])
        return (stdout, stderr, exitcode)

    def parse_repos(self):
        if not self.products:
            self.read_products()
        if not self.raw_repos:
            self.read_repos()
        self.repos = Repositories(self.raw_repos, self.products.arch())

    def read_repos(self):
        if self.is_connected:
            stdout, stderr, exitcode = self.run("zypper -x lr")

            if exitcode in (0, 106, 6):
                self.raw_repos = parse_repositories(stdout)
            else:
                logger.error(
                    f"Can't parse repositories on {self.hostname}, zypper returned {exitcode} exitcode"
                )
                logger.debug(f"output:\n {stderr}")
                raise ValueError(f"Can't read repositories on {self.hostname}:{self.port}")
        else:
            logger.debug(f"Host {self.hostname}:{self.port} not connected")

    def report_products(self, sink):
        return sink(self.hostname, self.port, self.products)

    def report_products_yaml(self, sink):
        return sink(self.hostname, self.products)

    def report_repos(self, sink):
        return sink(self.hostname, self.port, self.raw_repos)
