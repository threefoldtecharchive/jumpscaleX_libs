from urllib.parse import urlparse

import requests
from nacl.encoding import Base64Encoder

from Jumpscale import j

from .auth import HTTPSignatureAuth
from .errors import raise_for_status
from .farms import Farms
from .gateway import Gateway
from .nodes import Nodes
from .reservations import Reservations
from .users import Users

JSConfigClient = j.baseclasses.object_config


class Explorer(JSConfigClient):

    _SCHEMATEXT = """
        @url = tfgrid.explorer.client
        name** = "" (S)
        url = (S)
        """

    def _init(self, **kwargs):
        # load models
        self.url = self.url.rstrip("/")
        self._session = requests.Session()
        self._session.hooks = dict(response=raise_for_status)

        # configure authentication
        if j.me.tid and j.me.encryptor.private_key:
            secret = j.me.encryptor.signing_key.encode(Base64Encoder)
            auth = HTTPSignatureAuth(key_id=str(j.me.tid), secret=secret, headers=["(created)", "date", "threebot-id"])
            headers = {"threebot-id": str(j.me.tid)}
            self._session.auth = auth
            self._session.headers.update(headers)

        self.nodes = Nodes(self._session, self.url)
        self.users = Users(self._session, self.url)
        self.farms = Farms(self._session, self.url)
        self.reservations = Reservations(self._session, self.url)
        self.gateway = Gateway(self._session, self.url)
