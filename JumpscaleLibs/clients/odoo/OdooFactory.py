from Jumpscale import j
from .OdooClient import OdooClient

JSConfigs = j.baseclasses.object_config_collection
skip = j.baseclasses.testtools._skip


class OdooFactory(JSConfigs):

    __jslocation__ = "j.clients.odoo"
    _CHILDCLASS = OdooClient

    @skip("https://github.com/threefoldtech/jumpscaleX_libs/issues/80")
    def test(self):
        """
        kosmos 'j.clients.odoo.test()'
        :return:
        """
        cl = self.get()
        cl.login = "kristof@incubaid.com"
        cl.password_ = "1234"
        cl.database = "main"

        # cl.reset()

        cl.modules_default_install()

        j.shell()
