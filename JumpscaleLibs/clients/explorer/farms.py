from Jumpscale import j


class Farms:
    def __init__(self, session, url):
        self._session = session
        self._base_url = url
        j.data.schema.add_from_path(
            "/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/directory/models"
        )
        self._model = j.data.schema.get_from_url("tfgrid.directory.farm.1")

    def list(self, threebot_id=None):
        url = self._base_url + "/farms"
        if threebot_id:
            url += f"?owner={threebot_id}"
        resp = self._session.get(url)
        farms = []
        for farm_data in resp.json():
            farm = self._model.new(datadict=farm_data)
            farms.append(farm)
        return farms

    def new(self):
        return self._model.new()

    def register(self, farm):
        resp = self._session.post(self._base_url + "/farms", json=farm._ddict)
        return resp.json()["id"]

    def get(self, farm_id):
        resp = self._session.get(self._base_url + f"/farms/{farm_id}")
        return self._model.new(datadict=resp.json())
