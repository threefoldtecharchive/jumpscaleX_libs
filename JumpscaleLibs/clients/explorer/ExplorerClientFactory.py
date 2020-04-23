from Jumpscale import j
from .client import Explorer

JSConfigs = j.baseclasses.object_config_collection


class ExplorerClientFactory(JSConfigs):
    __jslocation__ = "j.clients.explorer"
    _CHILDCLASS = Explorer

    def _init(self, **kwargs):
        self._explorer = None
        basepath = j.core.tools.text_replace(
            "{DIR_CODE}/github/threefoldtech/jumpscaleX_libs/JumpscaleLibs/clients/explorer/models/"
        )
        j.data.schema.add_from_path(basepath)

    def default_addr_set(self, value):
        j.core.myenv.config["EXPLORER_ADDR"] = value
        j.core.myenv.config_save()
        if self._explorer:
            self._explorer = self.get(name="explorer", url=self._get_url(value), reload=True)
            self._explorer._init()  # force reload

    def _get_url(self, addr):
        proto = "http" if ":" in addr else "https"
        return f"{proto}://{addr}/explorer"

    @property
    def default(self):
        if not self._explorer:
            addr = j.core.myenv.config.get("EXPLORER_ADDR", "localhost")

            # please don't restore it it will get assertion error as obj._schema not equal schema
            # at: https://github.com/threefoldtech/jumpscaleX_core/issues/718
            self._explorer = self.get(name="explorer", url=self._get_url(addr))
        return self._explorer
