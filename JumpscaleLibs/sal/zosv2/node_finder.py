from Jumpscale import j
import netaddr

from .network import is_private


class NodeFinder:
    def __init__(self, explorer):
        self._actor_directory = explorer.actors_get("tfgrid.directory")

    def filter_is_up(self, node):
        """
        filter out nodes that have not received update for more then 10 minutes
        """
        ago = j.data.time.epoch - (60 * 10)
        return node.updated > ago

    def filter_public_ip4(self, node):
        return filter_public_ip(node, 4)

    def filter_public_ip6(self, node):
        return filter_public_ip(node, 6)

    def nodes_search(self, farm_id=None, country=None, city=None, cru=None, sru=None, mru=None, hru=None):
        """
        list return all the nodes
        
        :return: list of nodes
        :rtype: list
        """
        return self._actor_directory.nodes.list(
            farm_id=farm_id, country=country, city=city, cru=cru, sru=sru, mru=mru, hru=hru
        ).nodes


def filter_public_ip(node, version):
    if version not in [4, 6]:
        raise j.exceptions.Input("ip version can only be 4 or 6")

    ips = []

    # gather all the public ip of the requried version in ips
    if node.public_config and node.public_config.master:
        if version == 4:
            ips = [node.public_config.ipv4]
        else:
            ips = [node.public_config.ipv6]
    else:
        for iface in node.ifaces:
            for addr in iface.addrs:
                ip = netaddr.IPNetwork(addr)
                if ip.version != version:
                    continue
                ips.append(ip)
    # check if any of the ips is public
    for ip in ips:
        if not is_private(ip):
            return True
    return False
