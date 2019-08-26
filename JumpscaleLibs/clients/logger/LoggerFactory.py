from Jumpscale import j
from .LoggerClient import LoggerClient


class LoggerFactory(j.baseclasses.object_config_collection_testtools):

    __jslocation__ = "j.clients.logger"
    _CHILDFACTORY_CLASS = SSHClientBase

    def test(self, name="base"):
        """
        kosmos 'j.tools.logger.test()'
        """
        self._test_run(name=name)
