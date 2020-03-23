from Jumpscale import j
from .pagination import get_page, get_all


class Farms:
    def __init__(self, session, url):
        self._session = session
        self._base_url = url
        j.data.schema.add_from_path(
            "/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/directory/models"
        )
        self._model = j.data.schema.get_from_url("tfgrid.directory.farm.1")

    def list(self, threebot_id=None, page=None):
        url = self._base_url + "/farms"

        query = {}
        if threebot_id:
            query["owner"] = threebot_id

        if page:
            farms, _ = get_page(self._session, page, self._model, url, query)
        else:
            farms = list(self.iter(threebot_id))

        return farms

    def iter(self, threebot_id=None):
        url = self._base_url + "/farms"
        query = {}
        if threebot_id:
            query["owner"] = threebot_id
        yield from get_all(self._session, self._model, url, query)

    def new(self):
        return self._model.new()

    def register(self, farm):
        resp = self._session.post(self._base_url + "/farms", json=farm._ddict)
        return resp.json()["id"]

    def get(self, farm_id):
        resp = self._session.get(self._base_url + f"/farms/{farm_id}")
        return self._model.new(datadict=resp.json())
