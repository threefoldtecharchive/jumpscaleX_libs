from Jumpscale import j
from .GraphiteClient import GraphiteClient

JSConfigs = j.baseclasses.object_config_collection


class GraphiteFactory(JSConfigs):

    __jslocation__ = "j.clients.graphite"
    _CHILDCLASS = GraphiteClient
