# Usage example

## Create a network on all the nodes of a farm

```python
zos = j.sal.zosv2

# create a reservation
r = zos.reservation_create()
# create a network and add it to the reservation
network = zos.network.create(r, ip_range="172.24.0.0/16", network_name="zaibon_testnet_0")

# find all node from farm 1
nodes = zos.nodes_finder.nodes_search(farm_id=1)
# add each node into the network
for i, node in enumerate(nodes):
    iprange = f"172.24.{i+2}.0/24"
    zos.network.add_node(network, node.node_id, iprange)

# find a node that is public and has ipv4 public IP
node = next(filter(zos.nodes_finder.filter_public_ip4, nodes))
# add an external peer to the network for user laptop access using the public node as entrypoint
# we store the result of this command cause this is the configuration the user has to use to connect to
# the network from his laptop
wg_config = zos.network.add_access(network, node.node_id, "172.24.100.0/24", ipv4=True)


expiration = j.data.time.epoch + (3600 * 24 * 365)
# register the reservation
rid = zos.reservation_register(r, expiration)
time.sleep(5)
# inspect the result of the reservation provisioning
result = zos.reservation_result(rid)

print("wireguard configuration")
print(wg_config)
print("provisioning result")
print(result)
```

## create a container

```python
zos = j.sal.zosv2

# create a reservation
r = zos.reservation_create()
# add container reservation into the reservation
zos.container.create(reservation=r,
                    node_id='2fi9ZZiBGW4G9pnrN656bMfW6x55RSoHDeMrd9pgSA8T',
                    network_name='zaibon_testnet_0', # this assume this network is already provisioned on the node
                    ip_address='172.24.1.10',
                    flist='https://hub.grid.tf/zaibon/zaibon-ubuntu-ssh-0.0.2.flist',
                    entrypoint='/sbin/my_init')

expiration = j.data.time.epoch + (3600 * 24 * 365)
# register the reservation
rid = zos.reservation_register(r, expiration)
time.sleep(5)
# inspect the result of the reservation provisioning
result = zos.reservation_result(rid)

print("provisioning result")
print(result)
```

## create k8s cluster

```python
zos = j.sal.zosv2
r = zos.reservation_create()

cluster_secret = 'supersecret'
size = 1
network_name = 'zaibon_testnet_0'
sshkeys = ['ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMtml/KgilrDqSeFDBRLImhoAfIqikR2N9XH3pVbb7ex zaibon@tesla']

master = zos.kubernetes.add_master(
    reservation=r,
    node_id='2fi9ZZiBGW4G9pnrN656bMfW6x55RSoHDeMrd9pgSA8T',
    network_name=network_name,
    cluster_secret=cluster_secret,
    ip_address='172.24.1.20',
    size=size,
    sshkeys=sshkeys)


worker = zos.kubernetes.add_worker(
    reservation=r,
    node_id='72CP8QPhMSpF7MbSvNR1TYZFbTnbRiuyvq5xwcoRNAib',
    network_name=network_name,
    cluster_secret=cluster_secret,
    ip_address='172.24.2.20',
    size=size,
    master_ip=master.ipaddress,
    sshkeys=sshkeys)

expiration = j.data.time.epoch + (3600 * 24 * 365)
# register the reservation
rid = zos.reservation_register(r, expiration)
time.sleep(120)
# inspect the result of the reservation provisioning
result = zos.reservation_result(rid)

print("provisioning result")
print(result)
```