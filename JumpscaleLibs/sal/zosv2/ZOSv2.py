import netaddr
from Jumpscale import j

from .container import ContainerGenerator
from .id import _next_workload_id
from .kubernetes import K8sGenerator
from .network import NetworkGenerator
from .node_finder import NodeFinder
from .volumes import VolumesGenerator
from .zdb import ZDBGenerator


class Zosv2(j.baseclasses.object):
    __jslocation__ = "j.sal.zosv2"

    def _init(self, **kwargs):
        self._explorer = j.clients.threebot.explorer
        self._nodes_finder = NodeFinder(self._explorer)
        self._network = NetworkGenerator(self._explorer)
        self._container = ContainerGenerator()
        self._volume = VolumesGenerator()
        self._zdb = ZDBGenerator()
        self._kuberntes = K8sGenerator()

    @property
    def network(self):
        return self._network

    @property
    def container(self):
        return self._container

    @property
    def volume(self):
        return self._volume

    @property
    def zdb(self):
        return self._zdb

    @property
    def kubernetes(self):
        return self._kubernetes

    @property
    def nodes_finder(self):
        return self._nodes_finder

    def reservation_create(self):
        """
        creates a new empty reservation schema
        
        :return: reservation (tfgrid.workloads.reservation.1)
        :rtype: BCDBModel
        """
        reservation_model = j.data.schema.get_from_url("tfgrid.workloads.reservation.1")
        reservation = reservation_model.new()
        return reservation

    def reservation_register(self, reservation, expiration_date, identity=None, expiration_provisioning=None):
        me = identity if identity else j.tools.threebot.me.default
        reservation.customer_tid = me.tid

        if expiration_provisioning is None:
            expiration_provisioning = j.data.time.epoch + (60 * 10)  # 10 minutes
        reservation.data_reservation.expiration_provisioning = expiration_provisioning
        reservation.data_reservation.expiration_reservation = expiration_date

        reservation.json = reservation.data_reservation._json
        reservation.customer_signature = me.nacl.sign_hex(reservation.json.encode())

        resp = self._explorer.actors_all.workload_manager.reservation_register(reservation)
        return resp.id

    def reservation_result(self, reservation_id):
        return self._explorer.actors_all.workload_manager.reservation_get(reservation_id).results
