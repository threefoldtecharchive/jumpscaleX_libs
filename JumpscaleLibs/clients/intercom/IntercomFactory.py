from .IntercomClient import IntercomClient
from Jumpscale import j


JSConfigs = j.baseclasses.factory


class Intercom(JSConfigs):

    __jslocation__ = "j.clients.intercom"
    _CHILDCLASS = IntercomClient
