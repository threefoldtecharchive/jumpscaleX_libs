from Jumpscale import j
from .GraphiteClient import GraphiteClient

JSConfigs = j.baseclasses.factory


class GraphiteFactory(JSConfigs):

    __jslocation__ = "j.clients.graphite"
    _CHILDCLASS = GraphiteClient
