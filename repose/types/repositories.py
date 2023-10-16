from collections import UserDict
from ..target.parsers import Product


def _parse_product(name, arch):
    parts = name.split(":")
    # TODO: more check for possible products
    return (None, None) if len(parts) != 4 else Product(parts[0], parts[1], arch)


class Repositories(UserDict):
    """Dictionary holding repositories on host"""

    def __init__(self, iterable, arch):
        """
        :param: iterable ... containing instances of Repository namedtuple
        :arch: architecture of target
        """
        self.data = {x.alias: _parse_product(x.name, arch) for x in iterable}
