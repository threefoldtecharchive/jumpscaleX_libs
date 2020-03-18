from Jumpscale import j
from os import path


class Workloads:
    def __init__(self, session, url):
        self._session = session
        self._base_url = url + "/reservations"
        j.data.schema.add_from_path(
            "/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/workloads/models"
        )
        self._model = j.data.schema.get_from_url("tfgrid.workloads.reservation.1")

    def reservation_create(self, reservation):
        data = j.data.serializers.json.dumps(reservation._ddict)
        self._session.post(self._base_url, data=data)
        return True

    def reservations_list(self):
        reservations = []
        resp = self._session.get(self._base_url)
        resp.raise_for_status()
        for r in resp.json():
            o = self._model.new(datadict=r)
            reservations.append(o)
        return reservations

    def reservation_get(self, reservation_id):
        url = self._base_url + f"/{reservation_id}"
        resp = self._session.get(url)
        resp.raise_for_status()
        return self._model.new(datadict=resp.json())

    def reservation_sign_provision(self, reservation_id, tid, signature):
        url = self._base_url + f"/{reservation_id}/sign/provision"
        data = j.data.serializers.json.dumps({"signature": signature, "tid": tid, "epoch": j.data.time.epoch,})
        resp = self._session.post(url, data=data)
        resp.raise_for_status()
        return True

    def reservation_sign_delete(self, reservation_id, tid, signature):
        url = self._base_url + f"/{reservation_id}/sign/delete"
        data = j.data.serializers.json.dumps({"signature": signature, "tid": tid, "epoch": j.data.time.epoch})
        resp = self._session.post(url, data=data)
        resp.raise_for_status()
        return True
