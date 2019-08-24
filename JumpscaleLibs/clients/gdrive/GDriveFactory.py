from Jumpscale import j
from .GDriveClient import GDriveClient

JSConfigs = j.baseclasses.objects_config_bcdb


class GDriveFactory(JSConfigs):

    __jslocation__ = "j.clients.gdrive"
    _CHILDCLASS = GDriveClient
