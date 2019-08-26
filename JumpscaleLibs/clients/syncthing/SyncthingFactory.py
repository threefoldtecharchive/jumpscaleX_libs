from Jumpscale import j
from .SyncthingClient import SyncthingClient

JSConfigs = j.baseclasses.object_config_collection


class SyncthingFactory(JSConfigs):
    __jslocation__ = "j.clients.syncthing"
    _CHILDFACTORY_CLASS = SyncthingClient
