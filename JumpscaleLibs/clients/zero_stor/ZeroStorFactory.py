from .ZeroStorClient import ZeroStorClient
from Jumpscale import j

JSBASE = j.baseclasses.object_config_collection


class ZeroStorFactory(JSBASE):
    __jslocation__ = "j.clients.zstor"
    _CHILDCLASS = ZeroStorClient
