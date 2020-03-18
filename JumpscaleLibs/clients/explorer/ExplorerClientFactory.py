from Jumpscale import j
from .client import Explorer

JSConfigs = j.baseclasses.object_config_collection


class ExplorerClientFactory(JSConfigs):
    __jslocation__ = "j.clients.explorer"
    _CHILDCLASS = Explorer
