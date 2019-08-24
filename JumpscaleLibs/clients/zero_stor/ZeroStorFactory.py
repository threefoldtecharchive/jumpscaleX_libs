from .ZeroStorClient import ZeroStorClient
from Jumpscale import j

JSBASE = j.baseclasses.objects_config_bcdb


class ZeroStorFactory(JSBASE):
    __jslocation__ = "j.clients.zstor"
    _CHILDCLASS = ZeroStorClient
