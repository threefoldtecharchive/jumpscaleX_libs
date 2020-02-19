from Jumpscale import j
import netaddr
import ipaddress
import socket
from nacl import public
from nacl.encoding import Base64Encoder
class NetworkConfig:
    def __init__(self, private_key=None,public_key=None,wg_port=None, public_ip=None):
        self.private_key = private_key
        self.public_key = public_key
        self.wg_port = wg_port
        self.public_ip = public_ip

class Zosv2(j.baseclasses.object):
    __jslocation__ = "j.sal.zosv2"

    def _init(self, **kwargs):
        #j.clients.threebot.explorer_addr_set("explorer.testnet.grid.tf")
        self.explorer = j.clients.threebot.explorer
        self.config = NetworkConfig()

    # consider a node up if it has received update during the last 10 minute
    def is_up(self, node):
        ago = j.data.time.epoch - (60 * 10)
        return node.updated > ago

    def get_node(self,ip_version):
        #return node and public ip
        nodes = self.explorer.actors_all.nodes.list().nodes
        return self.find_node_public(nodes,ip_version)

    def find_node_public(self, nodes, version=6):
        # search a node that has a public ipv4 address
        for node in filter(self.is_up, nodes):
            for iface in node.ifaces:
                for addr in iface.addrs:
                    ip = ipaddress.ip_interface(addr).ip
                    if ip.version != version:
                        continue
                    if ip.is_global:
                        self.config.public_ip = str(ip)
                        return (node, str(ip))
        if version==4:
            for node in filter(self.is_up, nodes):
                ip = ipaddress.ip_interface(node.public_config.ipv4).ip
                if ip.is_global:
                    self.config.public_ip = str(ip)
                    return (node, str(ip))
            # need to check in ifaces
    def find_free_wg_port(self, node):
        ports = set(list(range(6000, 9000)))
        used = set(node.wg_ports)
        free = ports - used
        return free.pop()

    def new_reservation(self, user):
        reservation_model = j.data.schema.get_from_url("tfgrid.workloads.reservation.1")
        reservation = reservation_model.new()
        reservation.customer_tid = user.id
        reservation.data_reservation.expiration_provisioning = j.data.time.epoch + (60 * 10)  # 10 minutes
        reservation.data_reservation.expiration_reservation = j.data.time.epoch + (60 * 10)  # 10 minutes
        return  reservation

    def get_user(self,name,email):
        # should return error if doesn't exist
        return self.explorer.actors_all.phonebook.get(name=name, email=email)

    def check_ip_in_network(self, ip , network):
        return netaddr.IPAddress(ip) in netaddr.IPNetwork(network)

    def key_pair_get(self):
        wg_private = public.PrivateKey.generate()
        wg_public = wg_private.public_key

        wg_private_base64 = wg_private.encode(Base64Encoder)
        wg_public_base64 = wg_public.encode(Base64Encoder)

        return wg_private_base64, wg_public_base64

    def create_network(self,reservation,ip_range,node_id):
        network = reservation.data_reservation.networks.new()
        network.node_id = node_id
        network.workload_id = 1
        network.name = j.data.idgenerator.generateXCharID(16)
        network.iprange = ip_range
        return reservation , network

    def access_node(self, network, ip_range, node):
        network_range = netaddr.IPNetwork(ip_range).ip
        # add 256 to plus 1 in network from 172.20.0.0 -> 172.20.1.0
        network_range += 256
        network1 = str(network_range) + "/24"
        _, wg_private_encrypted, wg_public = j.tools.wireguard.generate_zos_keys(node.public_key_hex)
        wg_port = self.find_free_wg_port(node)

        nr1 = network.network_resources.new()

        nr1.iprange = network1
        nr1.node_id = node.node_id
        nr1.wireguard_listen_port = wg_port
        nr1.wireguard_public_key = wg_public
        nr1.wireguard_private_key_encrypted = wg_private_encrypted

        # add 256 to plus 1 in network from 172.20.0.0 -> 172.20.1.0
        network_range += 256
        network2 = str(network_range) + "/24"
        ip = netaddr.IPAddress(network_range)
        allowed_ip = ip.words

        private_key, public_key = self.key_pair_get()
        # add a peer to the network, this peer is your laptop
        peer = nr1.peers.new()
        peer.iprange = network2

        peer.allowed_iprange = ["100.64." + str(allowed_ip[1]) + "." + str(allowed_ip[2]) + "/32", network2]
        # this is your wireguard public key from your laptop
        peer.public_key = public_key.decode()

        self.config.public_key = public_key
        self.config.private_key = private_key
        self.config.wg_port = wg_port

        return network, self.config

    def add_volume(self,reservation, node_id, voulme_size=5, volume_type="SSD"):
        volume = reservation.data_reservation.volumes.new()
        volume.workload_id = 2
        volume.size = voulme_size
        volume.type = volume_type
        volume.node_id = node_id
        return  volume

    def get_all_ips(self, ip_range):
        networks = netaddr.IPNetwork(ip_range)
        ips = []
        for ip in list(networks.iter_hosts()):
           ips.append(ip.format())
        return ips

    def create_container(self,network_name,ip_address,node_id, reservation, flist, env={}, entrypoint="",interactive=False, volume_size=0, voulme_type="SSD", mount_point="/sandbox/var"):

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
            volume = self.add_volume(reservation,node_id,volume_size,voulme_type)
            vol = cont.volumes.new()
            # here we reference the volume created in the same reservation
            vol.workload_id = 3
            vol.volume_id = f"-{volume.workload_id}"
            vol.mountpoint = mount_point

        return reservation


    def wg_config(self, ip_range,network_config):

        first_network_range = netaddr.IPNetwork(ip_range).ip
        ip = netaddr.IPAddress(first_network_range)
        first_ip = ip.words
        # add 256 + 256 to 172.20.0.0 -> 172.20.2.0
        first_network_range += 512
        ip = netaddr.IPAddress(first_network_range)
        allowed_ip = ip.words

        result = f"""
        [Interface]
        Address = 100.64.{allowed_ip[1]}.{allowed_ip[2]}/16, {first_network_range}/16
        PrivateKey = {network_config.private_key.decode()}
        [Peer]
        PublicKey = {network_config.public_key.decode()}
        Endpoint = [{network_config.public_ip}]:{network_config.wg_port}
        AllowedIPs = {ip_range}, 100.64.{first_ip[1]}.{first_ip[2]}/16
        PersistentKeepalive = 25"""
        return result

    def register(self, reservation):
        reservation.json = reservation.data_reservation._json
        me = j.tools.threebot.me.default
        reservation.customer_signature = me.nacl.sign_hex(reservation.json.encode())

        resp = self.explorer.actors_all.workload_manager.reservation_register(reservation)
        return  resp.id

    def reservation_result(self, reservation_id):
        return self.explorer.actors_all.workload_manager.reservation_get(reservation_id).results
