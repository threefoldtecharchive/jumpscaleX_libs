from Jumpscale import j
from .GDriveClient import GDriveClient

JSConfigs = j.baseclasses.factory


class GDriveFactory(JSConfigs):

    __jslocation__ = "j.clients.gdrive"
    _CHILDCLASS = GDriveClient
