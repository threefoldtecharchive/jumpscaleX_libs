from .Sizes import Sizes


class Bytes(Sizes):
    """ converts numbers to power-of-2^2 representations (1024^0, 1024^1 ...)
    """

    _BASE = 1024.0

    __jslocation__ = "j.data_units.bytes"
