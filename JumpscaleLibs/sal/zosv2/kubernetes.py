from Jumpscale import j

from .crypto import encrypt_for_node
from .id import _next_workload_id


class K8sGenerator:
    def __init__(self, explorer):
        self._explorer = explorer

    def add_master(self, reservation, node_id, network_name, cluster_secret, ip_address, size, ssh_keys=[]):
        if size not in [1, 2]:
            raise j.exceptions.Input("size can only be 1 or 2")

        master = reservation.data_reservation.kubernetes.new()
        master.node_id = node_id
        master.workload_id = _next_workload_id(reservation)

        node = self._explorer.actors_all.nodes.get(node_id)
        master.cluster_secret = encrypt_for_node(node.public_key_hex, cluster_secret)
        master.network_id = network_name
        master.ipaddress = ip_address
        master.size = size
        if not isinstance(ssh_keys, list):
            ssh_keys = [ssh_keys]
        master.ssh_keys = ssh_keys

        return master

    def add_worker(self, reservation, node_id, network_name, cluster_secret, ip_address, size, master_ip, ssh_keys=[]):
        worker = self.add_master(
            reservation=reservation,
            node_id=node_id,
            network_name=network_name,
            cluster_secret=cluster_secret,
            ip_address=ip_address,
            size=size,
            ssh_keys=ssh_keys,
        )
        worker.master_ips = [master_ip]
        return worker
