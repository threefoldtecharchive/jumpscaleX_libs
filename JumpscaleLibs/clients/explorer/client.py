import requests

from .directory import Directory

from Jumpscale import j

JSConfigClient = j.baseclasses.object_config


class Explorer(JSConfigClient):

    _SCHEMATEXT = """
        @url = tfgrid.explorer.client
        name** = "" (S)
        url = (S)
        """

    def _init(self, **kwargs):
        self._session = requests.Session()
        # self.directory = Directory(self._session, self.url)
        self.workloads = Workloads(self._session, self.url)
        # self.phonebook = Phonebook(self._session, self.url)

