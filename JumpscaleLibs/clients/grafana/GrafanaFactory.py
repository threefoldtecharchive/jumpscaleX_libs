from Jumpscale import j
from .GrafanaClient import GrafanaClient


class GrafanaFactory(j.baseclasses.objects_config_bcdb):

    __jslocation__ = "j.clients.grafana"
    _CHILDCLASS = GrafanaClient

    def _init(self, **kwargs):
        self.clients = {}
