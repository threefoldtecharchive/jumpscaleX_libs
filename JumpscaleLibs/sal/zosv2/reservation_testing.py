from Jumpscale import j
import time
import random, uuid
import os
import pytest

WALLET_NAME = ""
WALLET_SECRET = ""

zos = j.sal.zosv2


def rand_string(size=10):
    return str(uuid.uuid4()).replace("-", "")[1:10]


def get_funded_wallet():
    if WALLET_NAME and WALLET_SECRET:
        wallet = j.clients.stellar.get(WALLET_NAME, network="Test", secret=WALLET_SECRET)
        return wallet
    else:
        raise ValueError("Please provide add Values to the global variables WALLET_NAME and WALLET_SECRET")


def create_new_wallet():
    wallet_name = j.data.idgenerator.generateXCharID(10)
    wallet = j.clients.stellar.new(wallet_name, network="Test")
    wallet.activate_through_friendbot()
    wallet.add_trustline("TFT", "GA47YZA3PKFUZMPLQ3B5F2E3CJIB57TGGU7SPCQT2WAEYKN766PWIMB3")
    return wallet


def get_wallet_balance(wallet, currency):
    coins = wallet.get_balance()
    tft_amount = [coin.balance for coin in coins.balances if coin.asset_code == currency][0]
    return float(tft_amount)


def check_if_wallet_refunded(wallet, expected_value, currency, timeout=60):
    t = time.time()
    while t + timeout > time.time():
        currency_amount = get_wallet_balance(wallet, currency)
        if expected_value == currency_amount:
            return True
        time.sleep(5)
    return False


def amount_paid_to_farmer(reservation_response):
    total_amount = sum([d.total_amount for d in reservation_response.escrow_information.details])
    total_amount = total_amount / 10e6
    return total_amount


def get_reservation_state(reservation_id):
    result = get_reservation_result(reservation_id, timeout=60)
    if result:
        return result[0].state
    return None


def get_reservation_result(reservation_id, timeout):
    def call_trial(func, *args, timeout=30):
        result = None
        t = time.time()
        while t + timeout > time.time():
            result = func(*args)
            if result:
                break
            time.sleep(3)
        return result

    result = call_trial(zos.reservation_result, reservation_id, timeout=timeout)
    return result


def reservation_payment(registered_reservation, currency):
    # . Get wallet
    wallet = get_funded_wallet()
    user_tft_amount = get_wallet_balance(wallet, currency)
    needed_currency_ammount = amount_paid_to_farmer(registered_reservation)
    if user_tft_amount < needed_currency_ammount:
        return False
    res = zos.billing.payout_farmers(wallet, registered_reservation)
    if not [t for t in wallet.list_transactions() if res[0] == t.hash]:
        return False
    return True


def create_network_reservation(network_name=""):
    r = zos.reservation_create()
    network_name = network_name | rand_string()
    ip_range = "172.17.0.0/16"
    network = zos.network.create(r, ip_range=ip_range, network_name=network_name)

    nodes = zos.nodes_finder.nodes_search()
    node = next(filter(zos.nodes_finder.filter_public_ip4, nodes))
    iprange = "172.24.{}.0/24".format(random.randint(3, 254))
    zos.network.add_node(network, node.node_id, iprange)
    expiration = j.data.time.epoch + (60 * 5)  # 5 mins
    registered_reservation = zos.reservation_register(r, expiration)
    return registered_reservation


def create_container_reservation(node_id, network_name):
    """
    create a container reservation
    """
    r = zos.reservation_create()
    zos.container.create(
        reservation=r,
        node_id=node_id,
        network_name=network_name,
        ip_address="172.24.1.{}".format(random.randint(3, 254)),
        flist="https://hub.grid.tf/zaibon/zaibon-ubuntu-ssh-0.0.2.flist",
        entrypoint="/sbin/my_init",
    )
    expiration = j.data.time.epoch + (60 * 5)  # 5 mins
    registered_reservation = zos.reservation_register(r, expiration)
    return registered_reservation


def create_storage_reservation():
    """
    create a storage reservation
    """
    r = zos.reservation_create()
    nodes = zos.nodes_finder.nodes_search(sru=10)
    node = random.choice(nodes)
    zos.zdb.create(
        reservation=r, node_id=node.node_id, size=10, mode="seq", password="supersecret", disk_type="SSD", public=False
    )
    expiration = j.data.time.epoch + (3600 * 24)
    registered_reservation = zos.reservation_register(r, expiration)
    return registered_reservation


def create_minio_container_reservation(network_name):
    """
    create a minio reservation
    """
    # Get a node where to reserve 0-db namespaces
    nodes = zos.nodes_finder.nodes_search(sru=10)
    nodes = list(filter(zos.nodes_finder.filter_is_up, nodes))
    z_db_node = random.choice(nodes)
    zdb_password = rand_string()

    # Get a node where to run the minio container itself
    minio_node = random.choice(nodes)

    # create a reservation for the 0-DBs
    reservation_storage = zos.reservation_create()
    # reservation some 0-db namespaces
    zos.zdb.create(
        reservation=reservation_storage,
        node_id=z_db_node.node_id,
        size=10,
        mode="seq",
        password=zdb_password,
        disk_type="SSD",
        public=False,
    )
    volume = zos.volume.create(reservation_storage, minio_node.node_id, size=10, type="SSD")
    expiration = j.data.time.epoch + (60 * 5)  # 5 mins
    zdb_rid = zos.reservation_register(reservation_storage, expiration)
    payment_result = reservation_payment(zdb_rid, "TFT")
    if not payment_result:
        return False  # payment fail
    results = get_reservation_result(zdb_rid.reservation_id, timeout=5)

    # Get the IP address of the 0-db namespaces after they are deployed ,we will need these IPs when creating the minio container
    namespace_config = []
    for result in results:
        data = j.data.serializers.json.loads(result.data_json)
        cfg = f"{data['Namespace']}:{zdb_password}@[{data['IP']}]:{data['Port']}"
        namespace_config.append(cfg)

    # create a reservation for the minio container
    reservation_container = zos.reservation_create()
    container = zos.container.create(
        reservation=reservation_container,
        node_id=minio_node.id,
        network_name=network_name,
        ip_address="172.24.1.{}".format(random.randint(3, 254)),
        flist="https://hub.grid.tf/tf-official-apps/minio-2020-01-25T02-50-51Z.flist",
        entrypoint="/bin/entrypoint",
        cpu=2,
        memory=2048,
        env={
            "SHARDS": ",".join(namespace_config),
            "DATA": "2",
            "PARITY": "1",
            "ACCESS_KEY": "minio",
            "SECRET_KEY": "passwordpassword",
        },
    )

    zos.volume.attach_existing(
        container=container, volume_id=f"{zdb_rid.reservation_id}-{volume.workload_id}", mount_point="/data"
    )

    minio_registered_reservation = zos.reservation_register(reservation_container, j.data.time.epoch + (60 * 60 * 3))
    return minio_registered_reservation


if __name__ == "__main__":
    if not (WALLET_NAME and WALLET_SECRET):
        raise ValueError("Please provide WALLET_NAME and WALLET_SECRET ")

    pytest.main(["-x", "reservation_testing.py"])
