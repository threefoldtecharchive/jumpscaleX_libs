from Jumpscale import j
import netaddr

from .network import is_private


class NodeFinder:
    def __init__(self, explorer):
        self._nodes = explorer.nodes
        self._farms = explorer.farms

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

    def nodes_by_capacity(
        self,
        farm_id=None,
        farm_name=None,
        country=None,
        city=None,
        cru=None,
        sru=None,
        mru=None,
        hru=None,
        currency=None,
    ):
        nodes = self.nodes_search(farm_id=farm_id, farm_name=farm_name, country=country, city=city)
        for node in nodes:
            total = node.total_resources
            reserved = node.reserved_resources
            if cru and total.cru - max(0, reserved.cru) < cru:
                continue

            if mru and total.mru - max(0, reserved.mru) < mru:
                continue

            if sru and total.sru - max(0, reserved.sru) < sru:
                continue

            if hru and total.hru - max(0, reserved.hru) < hru:
                continue

            if currency and currency == "FreeTFT" and not node.free_to_use:
                continue

            yield node

    def nodes_search(
        self, farm_id=None, country=None, city=None, cru=None, sru=None, mru=None, hru=None, farm_name=None
    ):
        """
        list return all the nodes

        :return: list of nodes
        :rtype: list
        """
        if farm_name:
            farms = self._farms.list(name=farm_name)
            if len(farms) != 1:
                raise j.exceptions.NotFound(f"Could not find farm with name {farm_name}")
            farm_id = farms[0].id

        return self._nodes.list(farm_id=farm_id, country=country, city=city, cru=cru, sru=sru, mru=mru, hru=hru)


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
