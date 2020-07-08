import netaddr
from Jumpscale import j

from .crypto import encrypt_for_node


class GatewayGenerator:
    def __init__(self, explorer):
        self._model_proxy = j.data.schema.get_from_url("tfgrid.workloads.reservation.gateway.proxy.1")
        self._model_reverse_proxy = j.data.schema.get_from_url("tfgrid.workloads.reservation.gateway.reverse_proxy.1")
        self._model_subdomain = j.data.schema.get_from_url("tfgrid.workloads.reservation.gateway.subdomain.1")
        self._model_delegate = j.data.schema.get_from_url("tfgrid.workloads.reservation.gateway.delegate.1")
        self._model_gateway4to6 = j.data.schema.get_from_url("tfgrid.workloads.reservation.gateway4to6.1")
        self._gateways = explorer.gateway

    def sub_domain(self, reservation, node_id, domain, ips, capacity_pool_id):
        for ip in ips:
            if not _is_valid_ip(ip):
                raise j.exceptions.Input(f"{ip} is not valid IP address")

        sb = self._model_subdomain.new()
        sb.info.pool_id = capacity_pool_id
        sb.info.node_id = node_id
        sb.info.workload_type = "SUBDOMAIN"
        sb.domain = domain
        sb.ips = ips

        reservation.workloads.append(sb)

        return sb

    def delegate_domain(self, reservation, node_id, domain, capacity_pool_id):
        d = self._model_delegate.new()
        d.info.pool_id = capacity_pool_id
        d.info.node_id = node_id
        d.info.workload_type = "SUBDOMAIN"
        d.domain = domain

        reservation.workloads.append(d)

        return d

    def tcp_proxy(self, reservation, node_id, domain, addr, port, capacity_pool_id, port_tls=None):
        p = self._model_proxy.new()
        p.info.pool_id = capacity_pool_id
        p.info.node_id = node_id
        p.info.workload_type = "PROXY"

        p.domain = domain
        p.addr = addr
        p.port = port
        p.port_tls = port_tls

        reservation.workloads.append(p)
        return p

    def tcp_proxy_reverse(self, reservation, node_id, domain, secret, capacity_pool_id):
        p = self._model_reverse_proxy.new()
        p.info.pool_id = capacity_pool_id
        p.info.node_id = node_id
        p.info.workload_type = "REVERSE-PROXY"

        p.domain = domain
        node = self._gateways.get(node_id)
        p.secret = encrypt_for_node(node.public_key_hex, secret)

        reservation.workloads.append(p)

        return p

    def gateway_4to6(self, reservation, node_id, public_key, capacity_pool_id):
        gw = self._model_gateway4to6.new()
        gw.info.pool_id = capacity_pool_id
        gw.info.node_id = node_id
        gw.info.workload_type = "GATEWAY4TO6"

        gw.public_key = public_key
        gw.node_id = node_id

        reservation.workloads.append(gw)

        return gw


def _is_valid_ip(ip):
    try:
        netaddr.IPAddress(ip)
        return True
    except:
        return False
