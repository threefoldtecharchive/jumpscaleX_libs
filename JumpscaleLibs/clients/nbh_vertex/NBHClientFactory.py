from Jumpscale import j

from .NBHClient import NBHClient

JSConfigBase = j.baseclasses.object_config_collection


class NBHClientFactory(j.baseclasses.object_config_collection_testtools):
    __jslocation__ = "j.clients.nbhvertex"
    _CHILDCLASS = NBHClient
