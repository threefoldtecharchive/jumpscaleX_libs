from Jumpscale import j
from os import path


class Reservations:
    def __init__(self, session, url):
        self._session = session
        self._base_url = url + "/reservations"
        j.data.schema.add_from_path(
            "/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/workloads/models"
        )
        self._model = j.data.schema.get_from_url("tfgrid.workloads.reservation.1")

    def new(self):
        return self._model.new()

    def create(self, reservation):
        resp = self._session.post(self._base_url, json=reservation._ddict)
        return resp.json()

    def list(self):
        reservations = []
        resp = self._session.get(self._base_url)
        for r in resp.json():
            o = self._model.new(datadict=r)
            reservations.append(o)
        return reservations

    def get(self, reservation_id):
        url = self._base_url + f"/{reservation_id}"
        resp = self._session.get(url)
        return self._model.new(datadict=resp.json())

    def sign_provision(self, reservation_id, tid, signature):
        url = self._base_url + f"/{reservation_id}/sign/provision"
        data = j.data.serializers.json.dumps({"signature": signature, "tid": tid, "epoch": j.data.time.epoch,})
        resp = self._session.post(url, data=data)
        return True

    def sign_delete(self, reservation_id, tid, signature):
        url = self._base_url + f"/{reservation_id}/sign/delete"
        data = j.data.serializers.json.dumps({"signature": signature, "tid": tid, "epoch": j.data.time.epoch})
        resp = self._session.post(url, data=data)
        return True
