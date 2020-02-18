from Jumpscale import j
import netaddr
import ipaddress
import socket

class Zosv2(j.baseclasses.object):
    __jslocation__ = "j.sal.zosv2"

    def _init(self, **kwargs):
        j.clients.threebot.explorer_addr_set("explorer.testnet.grid.tf")
        self.explorer = j.clients.threebot.explorer

    # consider a node up if it has received update during the last 10 minute
    def is_up(self, node):
        ago = j.data.time.epoch - (60 * 10)
        return node.updated > ago


    def find_node_public(self, nodes, version=6):
        # search a node that has a public ipv4 address
        if version == 6:
            for node in filter(self.is_up, nodes):
                for iface in node.ifaces:
                    for addr in iface.addrs:
                        ip = ipaddress.ip_interface(addr).ip
                        if ip.version != 6:
                            continue
                        if ip.is_global:
                            return (node, str(ip))
        else:
            for node in filter(self.is_up, nodes):
                ip = ipaddress.ip_interface(node.public_config.ipv4).ip
                if ip.is_global:
                    return (node, str(ip))
    def find_free_wg_port(self, node):
        ports = set(list(range(6000, 9000)))
        used = set(node.wg_ports)
        free = ports - used
        return free.pop()


    def check_ip_in_network(self, ip , network):

        networks = netaddr.IPNetwork(network)
        if netaddr.IPAddress(ip) in networks.iter_hosts():
            return True
        return False


    def key_pair_get(self):
        ex = j.tools.executor.get()

        rc, privatekey, err = ex.execute("wg genkey", showout=False)
        self.key_private_ = privatekey.strip()

        rc, publickey, err = ex.execute("echo {} | wg pubkey".format(privatekey.strip()), showout=False)
        self.key_public = publickey.strip()
        return self.key_private_, self.key_public

    def _network_configure(self, ip_range,reservation,node_id,wg_port,wg_public,wg_private_encrypted):
        # network
        network = reservation.data_reservation.networks.new()
        network.node_id = node_id
        network.workload_id = 1
        network.name = j.data.idgenerator.generateXCharID(16)
        network.iprange = ip_range

        network_range = netaddr.IPNetwork(ip_range).ip
        network_range += 256
        network1 = str(network_range) + "/24"

        nr1 = network.network_resources.new()

        nr1.iprange = network1
        nr1.node_id = node_id
        nr1.wireguard_listen_port = wg_port
        nr1.wireguard_public_key = wg_public
        nr1.wireguard_private_key_encrypted = wg_private_encrypted

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
        peer.public_key = public_key

        return  network, public_key, private_key

    def create_container(self,network_name,ip_address,node_id,reservation,password_corex="",user_corex="",pub_key=""):
        cont = reservation.data_reservation.containers.new()
        cont.node_id = node_id
        cont.workload_id = 3

        cont.flist = "https://hub.grid.tf/bola_nasr_1/threefoldtech-3bot-corex.flist"
        cont.storage_url = "zdb://hub.grid.tf:9900"
        cont.environment = {"corex_password":password_corex,"corex_user":user_corex,"pub_key":pub_key}
        cont.entrypoint = "/usr/bin/zinit init -d"
        cont.interactive = False

        net = cont.network_connection.new()
        net.network_id = network_name
        net.ipaddress = ip_address

        volume = reservation.data_reservation.volumes.new()
        volume.workload_id = 2
        volume.size = 10
        volume.type = "SSD"
        volume.node_id = node_id

        vol = cont.volumes.new()
        # here we reference the volume created in the same reservation
        vol.workload_id = 3
        vol.volume_id = f"-{volume.workload_id}"
        vol.mountpoint = "/sandbox/var"


    def wg_config(self, ip_range,public_ip,private_key,public_key,wg_port):
        first_network_range = netaddr.IPNetwork(ip_range).ip
        ip = netaddr.IPAddress(first_network_range)
        first_ip = ip.words

        first_network_range += 512
        ip = netaddr.IPAddress(first_network_range)
        allowed_ip = ip.words

        result = f"""[Interface]
                 Address = 100.64.{allowed_ip[1]}.{allowed_ip[2]}/16, {first_network_range}/16
                 PrivateKey = {private_key}
                 [Peer]
                 PublicKey = {public_key}
                 Endpoint = [{public_ip}]:{wg_port}
                 AllowedIPs = {ip_range}, 100.64.{first_ip[1]}.{first_ip[2]}/16
                 PersistentKeepalive = 25"""
        return result

    def reservation(self, name=None, email=None, ip_range =None, ip_address=None, pub_key=None, user_corex=None, password_corex=None):

        #should return error if doesn't exist
        me = self.explorer.actors_all.phonebook.get(name=name,email=email)

        nodes = self.explorer.actors_all.nodes.list().nodes

        hostname = socket.gethostname()
        IPAddr = socket.gethostbyname(hostname)
        i = ipaddress.ip_address(IPAddr)
        if i.version == 6:
            selected_node = self.find_node_public(nodes,6)
        else:
            selected_node = self.find_node_public(nodes, 4)

        if selected_node is None:
            raise j.exceptions.NotFound("no node found with public ipv%s"%i.version)

        node, public_ip = selected_node
        _, wg_private_encrypted, wg_public = j.tools.wireguard.generate_zos_keys(node.public_key_hex)
        wg_port = self.find_free_wg_port(node)

        reservation_model = j.data.schema.get_from_url("tfgrid.workloads.reservation.1")
        reservation = reservation_model.new()
        reservation.customer_tid = me.id
        reservation.data_reservation.expiration_provisioning = j.data.time.epoch + (60 * 10)  # 10 minutes
        reservation.data_reservation.expiration_reservation = j.data.time.epoch + (60 * 10)  # 10 minutes

        network, public_key, private_key = self._network_configure(ip_range,reservation,node.node_id,wg_port,wg_public,wg_private_encrypted)
        # volume

        self.create_container(network.name,ip_address,node.node_id,reservation,password_corex,user_corex,pub_key)

        reservation.json = reservation.data_reservation._json
        me = j.tools.threebot.me.default
        reservation.customer_signature = me.nacl.sign_hex(reservation.json.encode())

        resp = self.explorer.actors_all.workload_manager.reservation_register(reservation)
        result = self.wg_config(ip_range,public_ip,public_key,private_key,wg_port)
        return resp.id, result