from Jumpscale import j
import base58
from nacl import signing
from nacl import public
import binascii


class ContainerGenerator:
    def __init__(self):
        self._model = j.data.schema.get_from_url("tfgrid.workloads.reservation.container.1")

    def create(
        self,
        reservation,
        node_id,
        network_name,
        ip_address,
        flist,
        capacity_pool_id,
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
        cont = self._model.new()
        cont.info.node_id = node_id
        cont.info.workload_type = "CONTAINER"
        cont.info.pool_id = capacity_pool_id

        cont.flist = flist
        cont.storage_url = storage_url
        cont.environment = env
        cont.secret_environment = secret_env
        cont.entrypoint = entrypoint
        cont.interactive = interactive

        net = cont.network_connection.new()
        net.network_id = network_name
        net.ipaddress = ip_address
        net.public_ip6 = public_ipv6

        cont.capacity.cpu = cpu
        cont.capacity.memory = memory
        cont.capacity.disk_size = disk_size
        cont.capacity.disk_type = disk_type

        reservation.workloads.append(cont)

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
        """
        Add logs to the container of a reservation

        :param cont: container instance
        :type cont: tfgrid.workloads.reservation.container.1
        :param channel_type: type of channel the logs will be streamed to
        :type channel_type: str
        :param channel_host: IP of host that the logs will be streamed to
        :type channel_host: str
        :param channel_port: port of host that the logs will be streamed to
        :type channel_port: int
        :param channel_name: name of channel that will be published to
        :type channel_name: str
        :return: logs object added to the container
        :rtype: tfgrid.workloads.reservation.container.logs.1

        """
        cont_logs = cont.logs.new()
        cont_logs.type = channel_type
        cont_logs.data.stdout = f"redis://{channel_host}:{channel_port}/{channel_name}-stdout"
        cont_logs.data.stderr = f"redis://{channel_host}:{channel_port}/{channel_name}-stderr"
        return cont_logs
