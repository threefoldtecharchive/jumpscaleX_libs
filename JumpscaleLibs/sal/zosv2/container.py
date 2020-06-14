import netaddr
from Jumpscale import j
import base58
from nacl import signing
from .id import _next_workload_id
from nacl import public
import binascii


class ContainerGenerator:
    def create(
        self,
        reservation,
        node_id,
        network_name,
        ip_address,
        flist,
        env={},
        cpu=1,
        memory=1024,
        disk_size=256,
        disk_type="SSD",
        entrypoint="",
        interactive=False,
        secret_env={},
        public_ipv6=False,
        storage_url="zdb://hub.grid.tf:9900",
    ):
        """
        add a container to the reservation
        """

        cont = reservation.data_reservation.containers.new()
        cont.node_id = node_id
        cont.workload_id = _next_workload_id(reservation)

        cont.flist = flist
        cont.storage_url = storage_url
        cont.environment = env
        cont.secret_environment = secret_env
        cont.entrypoint = entrypoint
        cont.interactive = interactive

        nw = None
        for nw in reservation.data_reservation.networks:
            if nw.name == network_name:
                ip = netaddr.IPAddress(ip_address)
                subnet = netaddr.IPNetwork(nw.iprange)
                if ip not in subnet:
                    raise j.exceptions.Input(
                        f"ip address {str(ip)} is not in the range of the network resource of the node {str(subnet)}"
                    )

        net = cont.network_connection.new()
        net.network_id = network_name
        net.ipaddress = ip_address
        net.public_ip6 = public_ipv6

        cont.capacity.cpu = cpu
        cont.capacity.memory = memory
        cont.capacity.disk_size = disk_size
        cont.capacity.disk_type = disk_type

        return cont

    def corex_connect(self, ip, port=7681):
        """
        return a coreX client
        
        :param ip: ip address of the container
        :type ip: str
        :param port: listening port of corex process, defaults to 7681
        :type port: int, optional
        :return: j.clients.corex
        """
        return j.clients.corex.new(name=j.data.idgenerator.generateGUID(), addr=ip, port=port, autosave=False)

    def encrypt_secret(self, node_id, value):
        key = base58.b58decode(node_id)
        pk = signing.VerifyKey(key)
        encryption_key = pk.to_curve25519_public_key()

        box = public.SealedBox(encryption_key)
        result = box.encrypt(value.encode())

        return binascii.hexlify(result).decode()

    def add_logs(self, cont, channel_type, channel_host, channel_port, channel_name):
        cont_logs = cont.logs.new()
        cont_logs.type = channel_type
        cont_logs.data.stdout = f"redis://{channel_host}:{channel_port}/{channel_name}-stdout"
        cont_logs.data.stderr = f"redis://{channel_host}:{channel_port}/{channel_name}-stderr"
        return cont_logs
