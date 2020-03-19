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
        entrypoint="",
        interactive=False,
        secret_env={},
        public_ipv6=False,
        storage_url="zdb://hub.grid.tf:9900",
    ):
        """
        add a container to the reservation
        
        :param reservation: [description]
        :type reservation: [type]
        :param node_id: [description]
        :type node_id: [type]
        :param network_name: [description]
        :type network_name: [type]
        :param ip_address: [description]
        :type ip_address: [type]
        :param flist: [description]
        :type flist: [type]
        :param env: [description], defaults to {}
        :type env: dict, optional
        :param cpu: [description], defaults to 1
        :type cpu: int, optional
        :param memory: [description], defaults to 1024
        :type memory: int, optional
        :param entrypoint: [description], defaults to ""
        :type entrypoint: str, optional
        :param interactive: [description], defaults to False
        :type interactive: bool, optional
        :param storage_url: [description], defaults to "zdb://hub.grid.tf:9900"
        :type storage_url: str, optional
        :raises j.excpetions.Input: [description]
        :return: [description]
        :rtype: [type]
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
                    raise j.excpetions.Input(
                        f"ip address {str(ip)} is not in the range of the network resource of the node {str(subnet)}"
                    )

        net = cont.network_connection.new()
        net.network_id = network_name
        net.ipaddress = ip_address
        net.public_ip6 = public_ipv6

        cont.capacity.cpu = cpu
        cont.capacity.memory = memory

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
