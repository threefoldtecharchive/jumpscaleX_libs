from Jumpscale import j
from .client import Explorer

JSConfigs = j.baseclasses.object_config_collection


class ExplorerClientFactory(JSConfigs):
    __jslocation__ = "j.clients.explorer"
    _CHILDCLASS = Explorer

    def _init(self, **kwargs):
        self._explorer = None

    def default_addr_set(self, value):
        j.core.myenv.config["EXPLORER_ADDR"] = value
        j.core.myenv.config_save()
        self._explorer = None

    @property
    def default(self):
        if not self._explorer:
            url = j.core.myenv.config.get("EXPLORER_ADDR", "localhost")
            self._explorer = j.baseclasses.object_config_collection_testtools.get(self, name="explorer", url=url)
        return self._explorer
