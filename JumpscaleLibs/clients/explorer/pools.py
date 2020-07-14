from Jumpscale import j
from .pagination import get_page, get_all


class Pools:
    def __init__(self, client):
        self._session = client._session
        self._client = client
        self._model = j.data.schema.get_from_url("tfgrid.workloads.pool.1")
        self._model_create = j.data.schema.get_from_url("tfgrid.workloads.pool.create.1")
        self._model_created = j.data.schema.get_from_url("tfgrid.workloads.pool.created.1")

    @property
    def _base_url(self):
        return self._client.url + "/reservations/pools"

    def new(self):
        return self._model_create.new()

    def create(self, pool):
        resp = self._session.post(self._base_url, json=pool._ddict)
        return self._model_created.new(datadict=resp.json())

    def list(self, customer_tid=None, page=None):
        if page:
            reservations, _ = get_page(self._session, page, self._model, self._base_url)
        else:
            reservations = list(self.iter())
        return reservations

    def iter(self, customer_tid=None):
        tid = customer_tid if customer_tid else j.me.tid
        url = self._base_url + f"/owner/{tid}"
        yield from get_all(self._session, self._model, url)

    def get(self, pool_id):
        url = self._base_url + f"/{pool_id}"
        resp = self._session.get(url)
        return self._model.new(datadict=resp.json())
