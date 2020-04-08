import requests
from urllib.parse import urlparse

from .nodes import Nodes
from .users import Users
from .farms import Farms
from .reservations import Reservations
from .errors import raise_for_status

from Jumpscale import j

JSConfigClient = j.baseclasses.object_config


class Explorer(JSConfigClient):

    _SCHEMATEXT = """
        @url = tfgrid.explorer.client
        name** = "" (S)
        url = (S)
        """

    def _init(self, **kwargs):
        # load models
        basepath = "{DIR_CODE}/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/{pkgname}/models"
        j.data.schema.add_from_path(j.core.tools.text_replace(basepath, {"pkgname": "workloads"}))
        j.data.schema.add_from_path(j.core.tools.text_replace(basepath, {"pkgname": "phonebook"}))
        j.data.schema.add_from_path(j.core.tools.text_replace(basepath, {"pkgname": "directory"}))
        self._session = requests.Session()
        self._session.hooks = dict(response=raise_for_status)

        self.nodes = Nodes(self._session, self.url)
        self.users = Users(self._session, self.url)
        self.farms = Farms(self._session, self.url)
        self.reservations = Reservations(self._session, self.url)
        self._gateway = None

    @property
    def gateway(self):
        if self._gateway is None:
            parsedurl = urlparse(self.url)
            gedisclient = j.clients.gedis.get(
                name=f"{self.name}_gateway", host=parsedurl.hostname, package_name="tfgrid.gateway"
            )
            self._gateway = gedisclient.actors.gateway
        return self._gateway
