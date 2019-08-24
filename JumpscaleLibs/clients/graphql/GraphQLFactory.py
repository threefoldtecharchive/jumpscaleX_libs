from .GraphQLClient import GraphQLClient
from Jumpscale import j


JSConfigs = j.baseclasses.objects_config_bcdb


class GraphQLFactory(JSConfigs):

    __jslocation__ = "j.clients.graphql"
    _CHILDCLASS = GraphQLClient
