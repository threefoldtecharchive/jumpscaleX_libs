from Jumpscale import j

from .crypto import encrypt_for_node


class K8sGenerator:
    def __init__(self, explorer):
        self._model = j.data.schema.get_from_url("tfgrid.workloads.reservation.k8s.1")
        self._nodes = explorer.nodes

    def add_master(
        self, reservation, node_id, network_name, cluster_secret, ip_address, size, ssh_keys, capacity_pool_id
    ):
        if size not in [1, 2]:
            raise j.exceptions.Input("size can only be 1 or 2")

        master = self._model.new()
        master.info.pool_id = capacity_pool_id
        master.info.node_id = node_id
        master.info.workload_type = "kubernetes"

        node = self._nodes.get(node_id)
        master.cluster_secret = encrypt_for_node(node.public_key_hex, cluster_secret)
        master.network_id = network_name
        master.ipaddress = ip_address
        master.size = size
        if not isinstance(ssh_keys, list):
            ssh_keys = [ssh_keys]
        master.ssh_keys = ssh_keys

        reservation.workloads.append(master)

        return master

    def add_worker(
        self,
        reservation,
        node_id,
        network_name,
        cluster_secret,
        ip_address,
        size,
        master_ip,
        ssh_keys,
        capacity_pool_id,
    ):
        worker = self.add_master(
            reservation=reservation,
            node_id=node_id,
            network_name=network_name,
            cluster_secret=cluster_secret,
            ip_address=ip_address,
            size=size,
            ssh_keys=ssh_keys,
            capacity_pool_id=capacity_pool_id,
        )
        worker.master_ips = [master_ip]

        reservation.workloads.append(worker)

        return worker
