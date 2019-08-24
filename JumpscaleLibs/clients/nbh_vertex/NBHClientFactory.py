from Jumpscale import j

from .NBHClient import NBHClient

JSConfigBase = j.baseclasses.objects_config_bcdb


class NBHClientFactory(j.baseclasses.objects_config_bcdb):
    __jslocation__ = "j.clients.nbhvertex"
    _CHILDCLASS = NBHClient
