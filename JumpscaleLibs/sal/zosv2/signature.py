import hashlib
from io import StringIO, SEEK_END

from Jumpscale import j


def sign_workload(workload, signing_key):
    challenge = _hash_signing_challenge(workload)
    h = _hash(challenge)
    signature = signing_key.sign(h)
    return signature.signature


def sign_provision_request(workload, tid, signing_key):
    challenge = _hash_signing_challenge(workload)

    # append the user tid to the workload signing challenge
    b = StringIO(challenge)
    b.seek(0, SEEK_END)
    b.write("provision")
    b.write(str(tid))

    h = _hash(b.getvalue())
    signature = signing_key.sign(h)

    return signature.signature


def sign_delete_request(workload, tid, signing_key):
    challenge = _hash_signing_challenge(workload)

    # append the user tid to the workload signing challenge
    b = StringIO(challenge)
    b.seek(0, SEEK_END)
    b.write("delete")
    b.write(str(tid))

    h = _hash(b.getvalue())
    signature = signing_key.sign(h)

    return signature.signature


def _hash(challenge):
    if isinstance(challenge, str):
        challenge = challenge.encode("utf-8")

    h = hashlib.sha256(challenge)
    return h.digest()


def _hash_signing_challenge(workload):
    _encoders = {
        "ZDB": _zdb_challenge,
        "CONTAINER": _container_challenge,
        "VOLUME": _volume_challenge,
        # "network": _network_challenge,
        "KUBERNETES": _k8s_challenge,
        "PROXY": _proxy_challenge,
        "REVERSE-PROXY": _reverse_proxy_challenge,
        "SUBDOMAIN": _subdomain_challenge,
        "DOMAIN-DELEGATE": _delegate_challenge,
        "GATEWAY4TO6": _gateway4to6_challenge,
        "NETWORK_RESOURCE": _network_resource_challenge,
    }
    b = StringIO()
    b.write(_workload_info_challenge(workload.info))
    enc = _encoders.get(str(workload.info.workload_type))
    b.write(enc(workload))
    return b.getvalue()


def _workload_info_challenge(info):
    b = StringIO()
    b.write(str(info.workload_id))
    b.write(str(info.node_id))
    b.write(str(info.pool_id))
    b.write(str(info.reference))
    b.write(str(info.customer_tid))
    b.write(str(info.workload_type))
    b.write(str(info.epoch))
    b.write(str(info.description))
    b.write(str(info.metadata))
    return b.getvalue()


def _signing_request_challenge(sr):
    b = StringIO()
    for s in sr.signers:
        b.write(str(s))
    b.write(str(sr.quorum_min))
    return b.getvalue()


def _signature_challenge(s):
    b = StringIO()
    b.write(str(s.tid))
    b.write(str(s.signature))
    b.write(str(s.epoch))
    return b.getvalue()


def _container_challenge(container):
    b = StringIO()
    b.write(str(container.flist))
    b.write(str(container.hub_url))
    b.write(str(container.environment))
    b.write(str(container.entrypoint))
    b.write("true" if container.interactive else "false")
    for k, v in container.environment.items():
        b.write(f"{k}={v}")
    for k, v in container.secret_environment.items():
        b.write(f"{k}={v}")
    for v in container.volumes:
        b.write(str(v.volume_id))
        b.write(str(v.mountpoint))
    for nc in container.network_connection:
        b.write(str(nc.network_id))
        b.write(str(nc.ipaddress))
        b.write(str(nc.public_ip6))
    b.write(str(container.capacity.cpu))
    b.write(str(container.capacity.memory))
    b.write(str(container.capacity.disk_size))
    b.write(str(container.capacity.disk_type))
    return b.getvalue()


def _volume_challenge(volume):
    b = StringIO()
    b.write(str(volume.size))
    b.write(str(volume.type))
    return b.getvalue()


def _zdb_challenge(zdb):
    b = StringIO()
    b.write(str(zdb.size))
    b.write(str(zdb.mode))
    b.write(str(zdb.password))
    b.write(str(zdb.disk_type))
    b.write(str(zdb.public).lower())
    return b.getvalue()


def _k8s_challenge(k8s):
    b = StringIO()
    b.write(str(k8s.size))
    b.write(k8s.network_id)
    b.write(str(k8s.ipaddress))
    b.write(k8s.cluster_secret)
    for ip in k8s.master_ips:
        b.write(str(ip))
    for key in k8s.ssh_keys:
        b.write(key)
    return b.getvalue()


def _proxy_challenge(proxy):
    b = StringIO()
    b.write(str(proxy.domain))
    b.write(str(proxy.addr))
    b.write(str(proxy.port))
    b.write(str(proxy.port_tls))
    return b.getvalue()


def _reverse_proxy_challenge(reverse_proxy):
    b = StringIO()
    b.write(str(reverse_proxy.domain))
    b.write(str(reverse_proxy.secret))
    return b.getvalue()


def _subdomain_challenge(subdomain):
    b = StringIO()
    b.write(str(subdomain.domain))
    for ip in subdomain.ips:
        b.write(str(ip))
    return b.getvalue()


def _delegate_challenge(delegate):
    b = StringIO()
    b.write(str(delegate.domain))
    return b.getvalue()


def _gateway4to6_challenge(gateway4to6):
    b = StringIO()
    b.write(str(gateway4to6.public_key))
    return b.getvalue()


def _network_resource_challenge(network):
    b = StringIO()
    b.write(str(network.name))
    b.write(str(network.network_iprange))
    b.write(str(network.wireguard_private_key_encrypted))
    b.write(str(network.wireguard_public_key))
    b.write(str(network.wireguard_listen_port))
    b.write(str(network.iprange))
    for p in network.peers:
        b.write(str(p.public_key))
        b.write(str(p.endpoint))
        b.write(str(p.iprange))
    for iprange in p.allowed_iprange:
        b.write(str(iprange))
    return b.getvalue()


if __name__ == "__main__":
    zos = j.sal.zosv2

    model = j.data.schema.get_from_url("tfgrid.workloads.reservation.info.1")
    info = model.new()
    info.workload_id = 1
    info.node_id = "node1"
    info.pool_id = 1
    info.description = "workload info"
    info.customer_tid = 1
    info.customer_signature = "asdasdad"
    info.next_action = "DEPLOY"
    info.signing_request_provision.signers = [1, 2, 4]
    info.signing_request_provision.quorum_min = 2
    info.signing_request_delete.singers = [1, 2, 4]
    info.signing_request_delete.quorum_min = 2
    s = info.signatures_farmer.new()
    s.tid = 1
    s.signature = "asdasd"
    s.epoch = 123123
    s = info.signatures_delete.new()
    s.tid = 1
    s.signature = "asdasd"
    s.epoch = 123123
    info.epoch = 123123123
    info.metadata = "asdasd"
    info.workload_type = "VOLUME"
    print(workload_info_challenge(info))

    model = j.data.schema.get_from_url("tfgrid.workloads.reservation.volume.1")
    volume = model.new()
    volume.size = 10
    volume.type = "HDD"
    print(volume_challenge(volume))

    model = j.data.schema.get_from_url("tfgrid.workloads.reservation.zdb.1")
    zdb = model.new()
    zdb.disk_type = "SSD"
    zdb.size = 10
    zdb.mode = "SEQ"
    zdb.public = True
    print(zdb_challenge(zdb))

    model = j.data.schema.get_from_url("tfgrid.workloads.reservation.k8s.1")
    k8s = model.new()
    k8s.size = 10
    k8s.network_id = "network1"
    k8s.ipaddress = "192.128.1.10"
    k8s.cluster_secret = "supersecret"
    k8s.master_ips = ["192.168.1.1"]
    k8s.ssh_keys = ["rsa-secret"]
    print(k8s_challenge(k8s))

    model = j.data.schema.get_from_url("tfgrid.workloads.reservation.gateway.proxy.1")
    proxy = model.new()
    proxy.domain = "domain"
    proxy.addr = "192.126.0.1"
    proxy.port = 80
    proxy.port_tls = 443
    print(proxy_challenge(proxy))

    model = j.data.schema.get_from_url("tfgrid.workloads.reservation.gateway.reverse_proxy.1")
    reverse_proxy = model.new()
    reverse_proxy.domain = "domain"
    reverse_proxy.secret = "secret"
    print(reverse_proxy_challenge(reverse_proxy))

    model = j.data.schema.get_from_url("tfgrid.workloads.reservation.gateway.subdomain.1")
    subdomain = model.new()
    subdomain.domain = "domain"
    subdomain.ips = ["192.268.0.1", "2a02:2788:864:1314:4b6d:a8cd:d604:af44"]
    print(subdomain_challenge(subdomain))

    model = j.data.schema.get_from_url("tfgrid.workloads.reservation.gateway.delegate.1")
    delegate = model.new()
    delegate.domain = "domain"
    print(delegate_challenge(delegate))

    model = j.data.schema.get_from_url("tfgrid.workloads.reservation.gateway4to6.1")
    gateway4to6 = model.new()
    gateway4to6.public_key = "rsa-secret"
    print(gateway4to6_challenge(gateway4to6))

    model = j.data.schema.get_from_url("tfgrid.workloads.network_resource.1")
    network = model.new()
    network.name = "network1"
    network.network_iprange = "192.168.10.0/16"
    network.wireguard_private_key_encrypted = "asdasdasd"
    network.wireguard_public_key = "asdasdasd"
    network.wireguard_listen_port = 1000
    network.subnet = "192.168.10.1/24"
    peer = network.peers.new()
    peer.public_key = "asdasdasd"
    peer.allowed_iprange = "192.168.10.0/16"
    peer.endpoint = "123.123.123.123:9000"
    peer.iprange = "192.168.10.2/24"
    print(network_resource_challenge(network))
