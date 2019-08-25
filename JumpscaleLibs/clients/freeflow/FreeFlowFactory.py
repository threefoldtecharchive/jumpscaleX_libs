from Jumpscale import j
from .FreeFlowClient import FreeFlowClient

JSConfigs = j.baseclasses.factory


class FreeFlowFactory(JSConfigs):
    __jslocation__ = "j.clients.freeflowpages"
    _CHILDCLASS = FreeFlowClient
