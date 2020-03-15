from Jumpscale import j
from .AlertsClient import AlertsClient


class AlertsFactory(j.baseclasses.object_config_collection_testtools):

    __jslocation__ = "j.clients.alerts"
    _CHILDCLASS = AlertsClient
