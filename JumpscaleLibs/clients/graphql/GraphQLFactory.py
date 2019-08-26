from .GraphQLClient import GraphQLClient
from Jumpscale import j


JSConfigs = j.baseclasses.object_config_collection


class GraphQLFactory(JSConfigs):

    __jslocation__ = "j.clients.graphql"
    _CHILDFACTORY_CLASS = GraphQLClient
