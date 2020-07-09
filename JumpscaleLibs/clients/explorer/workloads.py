from Jumpscale import j
from .pagination import get_page, get_all


class Decoder:
    """
    utility class used to decode the workload in 2 steps
    1st get the common field from the response
    2nd based on the workload type instantiate the proper schema
    """

    @classmethod
    def new(cls, datadict):
        obj = cls(data=datadict)
        return obj.workload()

    def __init__(self, data):
        self.data = data
        self._models = {
            "VOLUME": j.data.schema.get_from_url("tfgrid.workloads.reservation.volume.1"),
            "CONTAINER": j.data.schema.get_from_url("tfgrid.workloads.reservation.container.1"),
            "ZDB": j.data.schema.get_from_url("tfgrid.workloads.reservation.zdb.1"),
            "KUBERNETES": j.data.schema.get_from_url("tfgrid.workloads.reservation.k8s.1"),
            "PROXY": j.data.schema.get_from_url("tfgrid.workloads.reservation.gateway.proxy.1"),
            "REVERSE-PROXY": j.data.schema.get_from_url("tfgrid.workloads.reservation.gateway.reverse_proxy.1"),
            "SUBDOMAIN": j.data.schema.get_from_url("tfgrid.workloads.reservation.gateway.subdomain.1"),
            "DOMAIN-DELEGATE": j.data.schema.get_from_url("tfgrid.workloads.reservation.gateway.delegate.1"),
            "GATEWAY4TO6": j.data.schema.get_from_url("tfgrid.workloads.reservation.gateway4to6.1"),
            "NETWORK_RESOURCE": j.data.schema.get_from_url("tfgrid.workloads.network_resource.1"),
        }
        self._info = j.data.schema.get_from_url("tfgrid.workloads.reservation.info.1")

    def workload(self):
        info = self._info.new(datadict=self.data)
        model = self._models.get(str(info.workload_type))
        if not model:
            raise j.exceptions.Input("unsupported workload type %s" % info.workload_type)
        workload = model.new(datadict=self.data)
        workload.info = info
        return workload


class Workloads:
    def __init__(self, client):
        self._session = client._session
        self._client = client
        self._model_info = j.data.schema.get_from_url("tfgrid.workloads.reservation.info.1")
        # self._reservation_create_model = j.data.schema.get_from_url("tfgrid.workloads.reservation.create.1")

    @property
    def _base_url(self):
        return self._client.url + "/reservations/workloads"

    def new(self):
        return self._model_info.new()

    def create(self, workload):
        url = self._client.url + "/reservations"
        data = workload._ddict
        del data["info"]["result"]
        info = data.pop("info")
        data.update(info)
        resp = self._session.post(url, json=data)
        return resp.json().get("reservation_id")

    def list(self, customer_tid=None, next_action=None, page=None):
        url = self._client.url + "/workload"
        if page:
            query = {}
            if customer_tid:
                query["customer_tid"] = customer_tid
            if next_action:
                query["next_action"] = self._next_action(next_action)
            workloads, _ = get_page(self._session, page, Decoder, url, query)
        else:
            workloads = list(self.iter(customer_tid, next_action))

        return workloads

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

        url = self._client.url + "/workload"

        query = {}
        if customer_tid:
            query["customer_tid"] = customer_tid
        if next_action:
            query["next_action"] = self._next_action(next_action)
        yield from filter(filter_next_action, get_all(self._session, Decoder, url, query))

    def get(self, workload_id):
        url = url = self._client.url + f"/workload/{workload_id}"
        resp = self._session.get(url)
        return Decoder.new(datadict=resp.json())

    def sign_provision(self, workload_id, tid, signature):
        url = self._base_url + f"/{workload_id}/sign/provision"
        data = j.data.serializers.json.dumps({"signature": signature, "tid": tid, "epoch": j.data.time.epoch})
        self._session.post(url, data=data)
        return True

    def sign_delete(self, workload_id, tid, signature):
        url = self._client.url + f"/reservations/{workload_id}/sign/delete"

        if isinstance(signature, bytes):
            signature = j.data.hash.bin2hex(signature)
        print("signature",signature)
        data = j.data.serializers.json.dumps({"signature": signature, "tid": tid, "epoch": j.data.time.epoch})
        self._session.post(url, data=data)
        return True
