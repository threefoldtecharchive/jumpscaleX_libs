from Jumpscale import j
from .GrafanaClient import GrafanaClient


class GrafanaFactory(j.baseclasses.object_config_collection_testtools):

    __jslocation__ = "j.clients.grafana"
    _CHILDFACTORY_CLASS = GrafanaClient

    def _init(self, **kwargs):
        self.clients = {}
