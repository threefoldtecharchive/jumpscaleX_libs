"""
Client factory for the Goldchain network, js entry point
"""

from Jumpscale import j

from .GoldChainClient import GoldChainClient

from .GoldChainExplorerClient import GoldChainExplorerClient
from .types.Errors import ErrorTypes
from .GoldChainTypesFactory import GoldChainTypesFactory
from .GoldChainTime import GoldChainTime

JSConfigBaseFactory = j.baseclasses.object_config_collection_testtools


class GoldChainClientFactory(JSConfigBaseFactory):
    """
    Factory class to get a goldchain client object
    """

    __jslocation__ = "j.clients.goldchain"
    _CHILDCLASS = GoldChainClient

    def _init(self, **kwargs):
        self._explorer_client = GoldChainExplorerClient()
        self._types_factory = GoldChainTypesFactory()
        self._error_types = ErrorTypes()
        self._time = GoldChainTime()

    @property
    def time(self):
        return self._time

    @property
    def explorer(self):
        return self._explorer_client

    @property
    def types(self):
        return self._types_factory

    @property
    def errors(self):
        return self._error_types

    def test(self, name=""):
        """
        kosmos 'j.clients.goldchain.test()'
        :return:
        """
        self._test_run(name=name)
