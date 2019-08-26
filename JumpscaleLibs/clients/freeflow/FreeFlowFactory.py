from Jumpscale import j
from .FreeFlowClient import FreeFlowClient

JSConfigs = j.baseclasses.object_config_collection


class FreeFlowFactory(JSConfigs):
    __jslocation__ = "j.clients.freeflowpages"
    _CHILDFACTORY_CLASS = FreeFlowClient
