from Jumpscale import j
from .pagination import get_page, get_all


class Reservations:
    def __init__(self, session, url):
        self._session = session
        self._base_url = url + "/reservations"
        self._model = j.data.schema.get_from_url("tfgrid.workloads.reservation.1")
        self._reservation_create_model = j.data.schema.get_from_url("tfgrid.workloads.reservation.create.1")

    def new(self):
        return self._model.new()

    def create(self, reservation):
        resp = self._session.post(self._base_url, json=reservation._ddict)
        return self._reservation_create_model.new(datadict=resp.json())

    def list(self, page=None):
        if page:
            reservations, _ = get_page(self._session, page, self._model, self._base_url)
        else:
            reservations = list(self.iter())
        return reservations

    def iter(self):
        yield from get_all(self._session, self._model, self._base_url)

    def get(self, reservation_id):
        url = self._base_url + f"/{reservation_id}"
        resp = self._session.get(url)
        return self._model.new(datadict=resp.json())

    def sign_provision(self, reservation_id, tid, signature):
        url = self._base_url + f"/{reservation_id}/sign/provision"
        data = j.data.serializers.json.dumps({"signature": signature, "tid": tid, "epoch": j.data.time.epoch,})
        self._session.post(url, data=data)
        return True

    def sign_delete(self, reservation_id, tid, signature):
        url = self._base_url + f"/{reservation_id}/sign/delete"
        data = j.data.serializers.json.dumps({"signature": signature, "tid": tid, "epoch": j.data.time.epoch})
        self._session.post(url, data=data)
        return True
