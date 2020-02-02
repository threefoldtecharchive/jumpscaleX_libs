from Jumpscale import j
from .StellarClient import StellarClient

JSConfigs = j.baseclasses.object_config_collection


class StellarFactory(JSConfigs):
    __jslocation__ = "j.clients.stellar"
    _CHILDCLASS = StellarClient
