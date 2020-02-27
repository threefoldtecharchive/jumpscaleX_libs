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

# expiration = j.data.time.epoch + (3600 * 24 * 365)
expiration = j.data.time.epoch + (10*60)
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
    ssh_keys=sshkeys)


worker = zos.kubernetes.add_worker(
    reservation=r,
    node_id='72CP8QPhMSpF7MbSvNR1TYZFbTnbRiuyvq5xwcoRNAib',
    network_name=network_name,
    cluster_secret=cluster_secret,
    ip_address='172.24.2.20',
    size=size,
    master_ip=master.ipaddress,
    ssh_keys=sshkeys)

expiration = j.data.time.epoch + (3600 * 24 * 365)
# register the reservation
rid = zos.reservation_register(r, expiration)
time.sleep(120)
# inspect the result of the reservation provisioning
result = zos.reservation_result(rid)

print("provisioning result")
print(result)
```

## reserve 0-DB storage namespaces

```python
zos = j.sal.zosv2

# find some node that have 10 GiB of SSD disks
nodes = zos.nodes_finder.nodes_search(sru=10)

# create a reservation
r = zos.reservation_create()
# add container reservation into the reservation
zos.zdb.create(
    reservation=r,
    node_id=nodes[0].node_id,
    size=10,
    mode='seq',
    password='supersecret',
    disk_type="SSD",
    public=False)

expiration = j.data.time.epoch + (3600 * 24)
# register the reservation
rid = zos.reservation_register(r, expiration)
time.sleep(5)
# inspect the result of the reservation provisioning
result = zos.reservation_result(rid)

print("provisioning result")
print(result)
```


```python
password = "supersecret"

# first find the node where to reserve 0-db namespaces
nodes = zos.nodes_finder.nodes_search(sru=10)
nodes = list(filter(zos.nodes_finder.filter_is_up,nodes))
nodes = nodes[:3]

# create a reservation
r = zos.reservation_create()
# reservation some 0-db namespaces
for node in nodes:
    zos.zdb.create(
        reservation=r,
        node_id=node.node_id,
        size=10,
        mode='seq',
        password='supersecret',
        disk_type="SSD",
        public=False)

rid = zos.reservation_register(r, j.data.time.epoch+(60*60))
results = zos.reservation_result(rid)

# read the IP address of the 0-db namespaces after they are deployed
# we will need these IPs when creating the minio container
namespace_config = []
for result in results:
    data = j.data.serializers.json.loads(result.data_json)
    cfg = f"{data['Namespace']}:{password}@[{data['IP']}]:{data['Port']}"
    namespace_config.append(cfg)

# find a node where to run the minio container itself
# make sure this node is part of your overlay network
nodes = zos.nodes_finder.nodes_search(sru=10)
nodes = list(filter(zos.nodes_finder.filter_is_up,nodes))
minio_node = nodes[0]


zos.container.create(reservation=r,
    node_id="72CP8QPhMSpF7MbSvNR1TYZFbTnbRiuyvq5xwcoRNAib",
    network_name='zaibon_testnet_0', # this assume this network is already provisioned on the node
    ip_address='172.24.2.15',
    flist='"https://hub.grid.tf/azmy.3bot/minio.flist"',
    entrypoint='/bin/entrypoint',
    cpu=2,
    memory=2048,
    env={
        "SHARDS":','.join(namespace_config),
        "DATA":"2",
        "PARITY":"1",
        "ACCESS_KEY":"minio",
        "SECRET_KEY":"passwordpassword",
    })

rid = zos.reservation_register(r, j.data.time.epoch+(60*60))
results = zos.reservation_result(rid)
```