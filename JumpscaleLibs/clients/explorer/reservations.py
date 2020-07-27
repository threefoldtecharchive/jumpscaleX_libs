from Jumpscale import j
from .pagination import get_page, get_all
from urllib.parse import urlparse, urlunparse


class Reservations:
    def __init__(self, client):
        self._session = client._session
        self._client = client
        self._model = j.data.schema.get_from_url("tfgrid.workloads.reservation.1")
        self._reservation_create_model = j.data.schema.get_from_url("tfgrid.workloads.reservation.create.1")

    @property
    def _base_url(self):
        # we fallback on the legacy endpoint of the API
        # cause they are only endpoints for reservation there
        url_parts = list(urlparse(self._client.url))
        url_parts[2] = "/explorer/reservations"
        return urlunparse(url_parts)

    def list(self, customer_tid=None, next_action=None, page=None):
        if page:
            query = {}
            if customer_tid:
                query["customer_tid"] = customer_tid
            if next_action:
                query["next_action"] = self._next_action(next_action)
            reservations, _ = get_page(self._session, page, self._model, self._base_url, query)
        else:
            reservations = list(self.iter(customer_tid, next_action))
        return reservations

    def _next_action(self, next_action):
        if next_action:
            if isinstance(next_action, str):
                next_action = getattr(self.new().next_action, next_action.upper()).value
            if not isinstance(next_action, int):
                raise j.exceptions.Input("next_action should be of type int")
        return next_action

    def iter(self, customer_tid=None, next_action=None):
        def filter_next_action(reservation):
            if next_action is None:
                return True
            return reservation.next_action == next_action

        query = {}
        if customer_tid:
            query["customer_tid"] = customer_tid
        if next_action:
            query["next_action"] = self._next_action(next_action)
        yield from filter(filter_next_action, get_all(self._session, self._model, self._base_url, query))

    def get(self, reservation_id):
        url = self._base_url + f"/{reservation_id}"
        resp = self._session.get(url)
        return self._model.new(datadict=resp.json())
