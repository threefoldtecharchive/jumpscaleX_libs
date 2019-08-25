from Jumpscale import j
from .SyncthingClient import SyncthingClient

JSConfigs = j.baseclasses.factory


class SyncthingFactory(JSConfigs):
    __jslocation__ = "j.clients.syncthing"
    _CHILDCLASS = SyncthingClient
