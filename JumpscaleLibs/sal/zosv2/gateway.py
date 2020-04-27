from Jumpscale import j
import netaddr
from .id import _next_workload_id


class GatewayGenerator:
    def sub_domain(self, reservation, node_id, domain, ips):
        for ip in ips:
            if not _is_valid_ip(ip):
                raise j.exceptions.Input(f"{ip} is not valid IP address")

        sb = reservation.data_reservation.subdomains.new()
        sb.node_id = node_id
        sb.workload_id = _next_workload_id(reservation)
        sb.domain = domain
        sb.ips = ips
        return sb

    def delegate_domain(self, reservation, node_id, domain):
        d = reservation.data_reservation.domain_delegates.new()
        d.node_id = node_id
        d.workload_id = _next_workload_id(reservation)
        d.domain = domain
        return d

    def tcp_proxy(self, reservation, node_id, domain, addr, port, port_tls=None):
        p = reservation.data_reservation.proxies.new()
        p.node_id = node_id
        p.workload_id = _next_workload_id(reservation)
        p.domain = domain
        p.addr = addr
        p.port = port
        p.port_tls = port_tls
        return p

    def tcp_proxy_reverse(self, reservation, node_id, domain, secret):
        p = reservation.data_reservation.reserve_proxies.new()
        p.node_id = node_id
        p.domain = domain
        p.workload_id = _next_workload_id(reservation)
        p.secret = secret
        return p

    def gateway_4to6(self, reservation, node_id, public_key):
        gw = reservation.data_reservation.gateway4to6.new()
        gw.public_key = public_key
        gw.node_id = node_id
        gw.workload_id = _next_workload_id(reservation)
        return gw


def _is_valid_ip(ip):
    try:
        netaddr.IPAddress(ip)
        return True
    except:
        return False
