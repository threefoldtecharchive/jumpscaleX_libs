from .GraphQLClient import GraphQLClient
from Jumpscale import j


JSConfigs = j.baseclasses.factory


class GraphQLFactory(JSConfigs):

    __jslocation__ = "j.clients.graphql"
    _CHILDCLASS = GraphQLClient
