from nacl import public
from nacl.encoding import Base64Encoder

import netaddr
from Jumpscale import j

from .id import _next_workload_id
from .network import NetworkBuilder
from .node_finder import NodeFinder


class Zosv2(j.baseclasses.object):
    __jslocation__ = "j.sal.zosv2"

    def _init(self, **kwargs):
        self._explorer = j.clients.threebot.explorer
        self._nodes_finder = NodeFinder(self._explorer)
        self._network = NetworkBuilder(self._explorer)

    @property
    def network(self):
        return self._network

    def get_user(self, name, email):
        # should return error if doesn't exist
        return self._explorer.actors_all.phonebook.get(name=name, email=email)

    def check_ip_in_network(self, ip, network):
        return netaddr.IPAddress(ip) in netaddr.IPNetwork(network)

    def reservation_create(self):
        """
        creates a new empty reservation schema
        
        :return: reservation (tfgrid.workloads.reservation.1)
        :rtype: BCDBModel
        """
        reservation_model = j.data.schema.get_from_url("tfgrid.workloads.reservation.1")
        reservation = reservation_model.new()
        return reservation

    def add_volume(self, reservation, node_id, voulme_size=5, volume_type="SSD"):
        volume = reservation.data_reservation.volumes.new()
        volume.workload_id = 2
        volume.size = voulme_size
        volume.type = volume_type
        volume.node_id = node_id
        return volume

    def get_all_ips(self, ip_range):
        networks = netaddr.IPNetwork(ip_range)
        ips = []
        for ip in list(networks.iter_hosts()):
            ips.append(ip.format())
        return ips

    def create_container(
        self,
        network_name,
        ip_address,
        node_id,
        reservation,
        flist,
        env={},
        entrypoint="",
        interactive=False,
        volume_size=0,
        voulme_type="SSD",
        mount_point="/sandbox/var",
    ):

        cont = reservation.data_reservation.containers.new()
        cont.node_id = node_id
        cont.workload_id = 3

        cont.flist = flist
        cont.storage_url = "zdb://hub.grid.tf:9900"
        cont.environment = env
        cont.entrypoint = entrypoint
        cont.interactive = interactive

        net = cont.network_connection.new()
        net.network_id = network_name
        net.ipaddress = ip_address

        if volume_size > 0:
            volume = self.add_volume(reservation, node_id, volume_size, voulme_type)
            vol = cont.volumes.new()
            # here we reference the volume created in the same reservation
            vol.workload_id = 3
            vol.volume_id = f"-{volume.workload_id}"
            vol.mountpoint = mount_point

        return reservation

    def register(self, reservation, expiration_date, identity=None):
        me = identity if identity else j.tools.threebot.me.default
        reservation.customer_tid = me.tid

        reservation.data_reservation.expiration_provisioning = j.data.time.epoch + (60 * 10)  # 10 minutes
        reservation.data_reservation.expiration_reservation = expiration_date

        reservation.json = reservation.data_reservation._json
        reservation.customer_signature = me.nacl.sign_hex(reservation.json.encode())

        resp = self._explorer.actors_all.workload_manager.reservation_register(reservation)
        return resp.id

    def reservation_result(self, reservation_id):
        return self._explorer.actors_all.workload_manager.reservation_get(reservation_id).results
