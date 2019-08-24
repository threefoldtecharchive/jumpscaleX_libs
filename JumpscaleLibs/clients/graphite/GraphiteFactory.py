from Jumpscale import j
from .GraphiteClient import GraphiteClient

JSConfigs = j.baseclasses.objects_config_bcdb


class GraphiteFactory(JSConfigs):

    __jslocation__ = "j.clients.graphite"
    _CHILDCLASS = GraphiteClient
