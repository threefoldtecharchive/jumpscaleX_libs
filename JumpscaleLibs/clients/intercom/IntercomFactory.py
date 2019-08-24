from .IntercomClient import IntercomClient
from Jumpscale import j


JSConfigs = j.baseclasses.objects_config_bcdb


class Intercom(JSConfigs):

    __jslocation__ = "j.clients.intercom"
    _CHILDCLASS = IntercomClient
