from Jumpscale import j
from .AlertsClient import AlertsClient


class LoggerFactory(j.baseclasses.object_config_collection_testtools):

    __jslocation__ = "j.clients.alerts"
    _CHILDCLASS = AlertsClient

    def test(self, name="base"):
        """
        kosmos 'j.tools.alerts.test()'
        """
        self._test_run(name=name)
