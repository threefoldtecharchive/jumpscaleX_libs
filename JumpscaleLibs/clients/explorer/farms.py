from nacl.encoding import Base64Encoder

from Jumpscale import j

from .auth import HTTPSignatureAuth
from .pagination import get_all, get_page


class Farms:
    def __init__(self, session, url):
        self._session = session
        self._base_url = url
        self._model = j.data.schema.get_from_url("tfgrid.directory.farm.1")

    def list(self, threebot_id=None, name=None, page=None, identity=None):
        me = identity if identity else j.me
        secret = me.encryptor.signing_key.encode(Base64Encoder)

        auth = HTTPSignatureAuth(key_id=str(me.tid), secret=secret, headers=["(created)", "date", "threebot-id"])
        headers = {"threebot-id": str(me.tid)}

        url = self._base_url + "/farms"

        query = {}
        if threebot_id:
            query["owner"] = threebot_id
        if name:
            query["name"] = name

        if page:
            farms, _ = get_page(self._session, page, self._model, url, query=query, auth=auth, headers=headers)
        else:
            farms = list(self.iter(threebot_id, name, identity=identity))

        return farms

    def iter(self, threebot_id=None, name=None, identity=None):
        me = identity if identity else j.me
        secret = me.encryptor.signing_key.encode(Base64Encoder)

        auth = HTTPSignatureAuth(key_id=str(me.tid), secret=secret, headers=["(created)", "date", "threebot-id"])
        headers = {"threebot-id": str(me.tid)}

        url = self._base_url + "/farms"
        query = {}
        if threebot_id:
            query["owner"] = threebot_id
        if name:
            query["name"] = name
        yield from get_all(self._session, self._model, url, query=query, auth=auth, headers=headers)

    def new(self):
        return self._model.new()

    def register(self, farm):
        resp = self._session.post(self._base_url + "/farms", json=farm._ddict)
        return resp.json()["id"]

    def update(self, farm, identity=None):
        me = identity if identity else j.me
        secret = me.encryptor.signing_key.encode(Base64Encoder)

        auth = HTTPSignatureAuth(key_id=str(me.tid), secret=secret, headers=["(created)", "date", "threebot-id"])
        headers = {"threebot-id": str(me.tid)}

        self._session.put(self._base_url + f"/farms/{farm.id}", auth=auth, headers=headers, json=farm._ddict)
        return True

    def delete(self, farm_id, node_id, identity=None):
        me = identity if identity else j.me
        secret = me.encryptor.signing_key.encode(Base64Encoder)

        auth = HTTPSignatureAuth(key_id=str(me.tid), secret=secret, headers=["(created)", "date", "threebot-id"])
        headers = {"threebot-id": str(me.tid)}

        self._session.delete(self._base_url + f"/farms/{farm_id}/{node_id}", auth=auth, headers=headers)
        return True

    def get(self, farm_id=None, farm_name=None, identity=None):
        me = identity if identity else j.me
        secret = me.encryptor.signing_key.encode(Base64Encoder)

        auth = HTTPSignatureAuth(key_id=str(me.tid), secret=secret, headers=["(created)", "date", "threebot-id"])
        headers = {"threebot-id": str(me.tid)}

        self._session.delete(self._base_url + f"/farms/{farm_id}/{node_id}", auth=auth, headers=headers)
        return True

    def get(self, farm_id=None, farm_name=None):
        me = identity if identity else j.me
        secret = me.encryptor.signing_key.encode(Base64Encoder)

        auth = HTTPSignatureAuth(key_id=str(me.tid), secret=secret, headers=["(created)", "date", "threebot-id"])
        headers = {"threebot-id": str(me.tid)}

        if farm_name:
            for farm in self.iter(identity=identity):
                if farm.name == farm_name:
                    return farm
            else:
                raise j.exceptions.NotFound(f"Could not find farm with name {farm_name}")
        elif not farm_id:
            raise j.exceptions.Input("farms.get requires at least farm_id or farm_name")
        resp = self._session.get(self._base_url + f"/farms/{farm_id}", auth=auth, headers=headers)
        return self._model.new(datadict=resp.json())
