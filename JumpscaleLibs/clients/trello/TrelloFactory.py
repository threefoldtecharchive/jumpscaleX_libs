from Jumpscale import j
from .TrelloClient import TrelloClient

JSConfigs = j.baseclasses.object_config_collection
skip = j.baseclasses.testtools._skip


class Trello(JSConfigs):
    __jslocation__ = "j.clients.trello"
    _CHILDCLASS = TrelloClient

    def install(self, reset=False):
        j.builders.runtimes.python3.pip_package_install("py-trello", reset=reset)

    @skip("https://github.com/threefoldtech/jumpscaleX_libs/issues/84")
    def test(self):
        """
        kosmos 'j.clients.trello.test()'

        to configure:
        js_config configure -l j.clients.trello

        get appkey: https://trello.com/app-key

        """
        cl = self.get(name="main")
        cl.test()
