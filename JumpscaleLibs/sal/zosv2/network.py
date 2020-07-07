from nacl import public
from nacl.encoding import Base64Encoder
import random
import netaddr
from Jumpscale import j

from .id import _next_workload_id

"""
net = j.sal.zosv2._workload_network.create("10.10.0.0/16", "workload_net_1", 9)
j.sal.zosv2._workload_network.add_node(net, "qzuTJJVd5boi6Uyoco1WWnSgzTb7q8uN79AjBT9x9N3", "10.10.20.0/24")
wg = j.sal.zosv2._workload_network.add_access(net, "10.10.20.0/24", ipv4=True)
j.sal.zosv2._workloads.deploy(net, 9, 1594138070)
"""


class NetworkGenerator:
    def __init__(self, explorer):
        self._nodes = explorer.nodes
        self._farms = explorer.farms
        self._model = j.data.schema.get_from_url("tfgrid.workloads.network_resource.1")

    def _load_network(self, network):
        network.public_endpoints = get_endpoints(self._nodes.get(network.info.node_id))
        network.access_points = extract_access_points(network)

    def _cleanup_network(self, network):
        if hasattr(network, "public_endpoints"):
            delattr(network, "public_endpoints")

        if hasattr(network, "access_points"):
            delattr(network, "access_points")

    def create(self, ip_range, network_name, pool_id, customer_tid=None):
        """
                add a network into the reservation

                :param workload: root reservation object, the network will be added to it
                :type reservation: tfgrid.workloads.reservation.1
                :param ip_range: subnet of the network, it must have a network mask of /16
                :type ip_range: str
                :param network_name: identifier of the network, if not specified a randon name will be generated
                :type network_name: str, optional
                :return: new network object
                :rtype: tfgrid.workloads.reservation.1
                """
        network = netaddr.IPNetwork(ip_range)
        if not is_private(network):
            raise j.exceptions.Input("ip_range must be a private network range (RFC 1918)")
        if network.prefixlen != 16:
            raise j.exceptions.Input("network mask of ip range must be a /16")

        network = self._model.new()
        network.name = network_name if network_name else j.data.idgenerator.generateXCharID(16)
        network.iprange = ip_range
        network.info.pool_id = pool_id
        network.info.customer_tid = customer_tid if customer_tid else j.me.tid
        network.info.workload_type = "NETWORK_RESOURCE"
        return network

    def add_node(self, network, node_id, ip_range, wg_port=None):
        """
        add a 0-OS node into the network

        :param network: network object where to add the network resource
        :type network: tfgrid.workloads.reservation.network.1
        :param node_id: node_id of the node we want to add to the network
        :type node_id: str
        :param ip_range: subnet to attach to the network resource. network mask should be a /24 and be part of the network subnet
        :type ip_range: str
        :param wg_port: listening port of the wireguard interface, if None port will be selected automatically
        :type wg_port: int, optional
        """
        if not node_id:
            raise j.exceptions.Input("node_id cannot be none or empty")

        node = self._nodes.get(node_id)

        if netaddr.IPNetwork(ip_range).prefixlen != 24:
            raise j.exceptions.Input("ip_range should have a netmask of /24, not /%d", ip_range.prefixlen)

        if wg_port is None:
            wg_port = _find_free_wg_port(node)

        _, wg_private_encrypted, wg_public = j.tools.wireguard.generate_zos_keys(node.public_key_hex)

        network.iprange = ip_range
        network.info.node_id = node_id
        network.wireguard_listen_port = wg_port
        network.wireguard_public_key = wg_public
        network.wireguard_private_key_encrypted = wg_private_encrypted

        try:
            self._load_network(network)
            generate_peers(network)
        finally:
            self._cleanup_network(network)

    def add_access(self, network, ip_range, wg_public_key=None, ipv4=False):
        """
        add an external access to the network. use this function is you want to allow
        a member to your network that is not a 0-OS node. User laptop, external server,...

        :param network: network object where to add the network resource
        :type network: tfgrid.workloads.reservation.network.1
        :param ip_range: subnet to allocate to the member,  network mask should be a /24 and be part of the network subnet
        :type ip_range: str
        :param wg_public_key: public key of the new member. If none a new key pair will be generated automatically
        :type wg_public_key: str, optional
        :param ipv4: if True, the endpoint of the access node will use IPv4. Use this if the member is not IPv6 enabled
        :type ipv4: bool, optional
        :return: wg-quick configuration
        :rtype: str
        """

        if netaddr.IPNetwork(ip_range).prefixlen != 24:
            raise j.exceptions.Input("ip_range should have a netmask of /24, not /%d", ip_range.prefixlen)

        try:
            self._load_network(network)

            if len(network.public_endpoints) == 0:
                raise j.exceptions.Input("access node must have at least 1 public endpoint")

            endpoint = ""
            wg_port = network.wireguard_listen_port
            for ep in network.public_endpoints:
                if ipv4 and ep.version == 4:
                    endpoint = f"{str(ep.ip)}:{wg_port}"
                    break
                if not ipv4 and ep.version == 6:
                    ip = str(network.public_endpoints[0].ip)
                    endpoint = f"[{ip}]:{wg_port}"
                    break

            if not endpoint:
                raise j.exceptions.Input("access node has no public endpoint of the requested type")

            wg_private_key = None
            if wg_public_key is None:
                wg_private = public.PrivateKey.generate()
                wg_public = wg_private.public_key
                wg_private_key = wg_private.encode(Base64Encoder)
                wg_public_key = wg_public.encode(Base64Encoder)

            network.access_points.append(
                AccessPoint(node_id=network.info.node_id, subnet=ip_range, wg_public_key=wg_public_key, ip4=ipv4)
            )

            generate_peers(network)

        finally:
            self._cleanup_network(network)

        return generate_wg_quick(
            wg_private_key.decode(), ip_range, network.wireguard_public_key, network.iprange, endpoint
        )


def generate_peers(network):
    if has_ipv4(network):
        allowed_ips = [network.iprange, wg_routing_ip(network.iprange)]
        peer = network.peers.new()
        peer.iprange = str(network.iprange)
        for pep in network.public_endpoints:
            if pep.version == 4:
                peer.endpoint = f"{str(pep.ip)}.{network.wireguard_listen_port}"
                break
        peer.allowed_iprange = [str(x) for x in allowed_ips]
        peer.public_key = network.wireguard_public_key


def has_hidden_nodes(network):
    for nr in network.network_resources:
        if len(nr.public_endpoints) <= 0:
            return True
    return False


def find_public_node(network_resources):
    for nr in network_resources:
        if has_ipv4(nr):
            return nr
    return None


def has_ipv4(network_resource):
    for pep in network_resource.public_endpoints:
        if pep.version == 4:
            return True
    return False


def wg_routing_ip(ip_range):
    if not isinstance(ip_range, netaddr.IPNetwork):
        ip_range = netaddr.IPNetwork(ip_range)
    words = ip_range.ip.words
    return f"100.64.{words[1]}.{words[2]}/32"


def _find_free_wg_port(node):
    ports = set(list(range(1000, 9000)))
    used = set(node.wg_ports)
    free = ports - used
    return random.choice(tuple(free))


# a node has either a public namespace with []ipv4 or/and []ipv6 -or-
# some interface has received a SLAAC addr
# which has been registered in BCDB
def get_endpoints(node):
    ips = []
    if node.public_config and node.public_config.master:
        ips.append(netaddr.IPNetwork(node.public_config.ipv4))
        ips.append(netaddr.IPNetwork(node.public_config.ipv6))
    else:
        for iface in node.ifaces:
            for ip in iface.addrs:
                ips.append(netaddr.IPNetwork(ip))

    endpoints = []
    for ip in ips:
        if ip.is_unicast() and not is_private(ip):
            endpoints.append(ip)
    return endpoints


_private_networks = [
    netaddr.IPNetwork("127.0.0.0/8"),  # IPv4 loopback
    netaddr.IPNetwork("10.0.0.0/8"),  # RFC1918
    netaddr.IPNetwork("172.16.0.0/12"),  # RFC1918
    netaddr.IPNetwork("192.168.0.0/16"),  # RFC1918
    netaddr.IPNetwork("169.254.0.0/16"),  # RFC3927 link-local
    netaddr.IPNetwork("::1/128"),  # IPv6 loopback
    netaddr.IPNetwork("fe80::/10"),  # IPv6 link-local
    netaddr.IPNetwork("fc00::/7"),  # IPv6 unique local addr
    netaddr.IPNetwork("200::/7"),  # IPv6 yggdrasil range
]


def is_private(ip):
    if not isinstance(ip, netaddr.IPNetwork):
        ip = netaddr.IPNetwork(ip)
    for network in _private_networks:
        if ip in network:
            return True
    return False


def extract_access_points(network):
    # gather all actual nodes, using their wg pubkey as key in the map (NodeID
    # can't be seen in the actual peer struct)
    actual_nodes = {}
    actual_nodes[network.wireguard_public_key] = None

    aps = []
    for peer in network.peers:
        if peer.public_key not in actual_nodes:
            # peer is not a node so it must be external
            ap = AccessPoint(
                node_id=network.info.node_id,
                subnet=peer.iprange,
                wg_public_key=peer.public_key,
                # we can't infer if we use IPv6 or IPv4
            )
            aps.append(ap)
    return aps


class AccessPoint:
    def __init__(self, node_id, subnet, wg_public_key, ip4=None):
        self.node_id = node_id
        self.subnet = subnet
        self.wg_public_key = wg_public_key
        self.ip4 = ip4


def generate_wg_quick(wg_private_key, subnet, peer_wg_pub_key, allowed_ip, endpoint):
    address = wg_routing_ip(subnet)
    allowed_ips = [allowed_ip, wg_routing_ip(allowed_ip)]
    aip = ", ".join(allowed_ips)

    result = f"""
[Interface]
Address = {address}
PrivateKey = {wg_private_key}
[Peer]
PublicKey = {peer_wg_pub_key}
AllowedIPs = {aip}
PersistentKeepalive = 25
"""
    if endpoint:
        result += f"Endpoint = {endpoint}"

    return result
