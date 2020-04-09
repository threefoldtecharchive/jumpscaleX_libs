from nacl.encoding import Base64Encoder

from Jumpscale import j

from .auth import HTTPSignatureAuth
from .pagination import get_all, get_page


class Farms:
    def __init__(self, session, url):
        self._session = session
        self._base_url = url
        self._model = j.data.schema.get_from_url("tfgrid.directory.farm.1")

    def list(self, threebot_id=None, name=None, page=None):
        url = self._base_url + "/farms"

        query = {}
        if threebot_id:
            query["owner"] = threebot_id
        if name:
            query["name"] = name

        if page:
            farms, _ = get_page(self._session, page, self._model, url, query)
        else:
            farms = list(self.iter(threebot_id, name))

        return farms

    def iter(self, threebot_id=None, name=None):
        url = self._base_url + "/farms"
        query = {}
        if threebot_id:
            query["owner"] = threebot_id
        if name:
            query["name"] = name
        yield from get_all(self._session, self._model, url, query)

    def new(self):
        return self._model.new()

    def register(self, farm):
        resp = self._session.post(self._base_url + "/farms", json=farm._ddict)
        return resp.json()["id"]

    def update(self, farm, identity=None):
        me = identity if identity else j.tools.threebot.me.default
        secret = me.nacl.signing_key.encode(Base64Encoder)

        auth = HTTPSignatureAuth(key_id=str(me.tid), secret=secret, headers=["(created)", "date", "threebot-id"])
        headers = {"threebot-id": str(me.tid)}

        self._session.put(self._base_url + f"/farms/{farm.id}", auth=auth, headers=headers, json=farm._ddict)
        return True

    def get(self, farm_id=None, farm_name=None):
        if farm_name:
            for farm in self.iter():
                if farm.name == farm_name:
                    return farm
            else:
                raise j.exceptions.NotFound(f"Could not find farm with name {farm_name}")
        elif not farm_id:
            raise j.exceptions.Input("farms.get requires at least farm_id or farm_name")
        resp = self._session.get(self._base_url + f"/farms/{farm_id}")
        return self._model.new(datadict=resp.json())
