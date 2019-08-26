from Jumpscale import j

from .NBHClient import NBHClient

JSConfigBase = j.baseclasses.factory


class NBHClientFactory(j.baseclasses.factory):
    __jslocation__ = "j.clients.nbhvertex"
    _CHILDFACTORY_CLASS = NBHClient
