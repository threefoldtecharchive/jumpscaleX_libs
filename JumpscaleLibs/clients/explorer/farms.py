from Jumpscale import j


class Farms:
    def __init__(self, session, url):
        self._session = session
        self._base_url = url
        j.data.schema.add_from_path(
            "/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/directory/models"
        )
        self._farm_model = j.data.schema.get_from_url("tfgrid.directory.farm.1")

    def list(self):
        resp = self._session.get(self._base_url + "/farms")
        resp.raise_for_status()
        farms = []
        for farm_data in resp.json():
            farm = self._farm_model.new(datadict=farm_data)
            farms.append(farm)
        return farms

    def new(self):
        return self._farm_model.new()

    def register(self, farm):
        resp = self._session.post(self._base_url + "/farms", json=farm._dict)
        resp.raise_for_status()
        return resp.json()

    def get(self, farm_id):
        resp = self._session.get(self._base_url + f"/farm/{farm_id}")
        resp.raise_for_status()
        return self._farm_model.new(datadict=resp.json())