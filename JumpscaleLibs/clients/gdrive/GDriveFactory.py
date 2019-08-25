from Jumpscale import j
from .GDriveClient import GDriveClient

JSConfigs = j.baseclasses.object_config_collection


class GDriveFactory(JSConfigs):

    __jslocation__ = "j.clients.gdrive"
    _CHILDCLASS = GDriveClient
