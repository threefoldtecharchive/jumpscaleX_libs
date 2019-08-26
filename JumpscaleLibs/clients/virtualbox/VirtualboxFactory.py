from time import sleep

from Jumpscale import j

from .VirtualboxClient import VirtualboxClient

JSBASE = j.baseclasses.object_config_collection


class VirtualboxFactory(j.baseclasses.object):
    __jslocation__ = "j.clients.virtualbox"

    def _init(self, **kwargs):

        self._client = None

    def get(self):
        return self.client

    @property
    def client(self):
        if self._client == None:
            self._client = VirtualboxClient()
        return self._client
