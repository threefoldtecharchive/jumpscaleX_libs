from Jumpscale import j
import time
import random
import os
import pytest

WALLET_NAME = ""
WALLET_SECRET = ""

zos = j.sal.zosv2


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
    return wallet


def get_wallet_balance(wallet):
    coins = wallet.get_balance()
    tft_amount = [coin.balance for coin in coins.balances if coin.asset_code == "TFT"][0]
    return float(tft_amount)


def check_if_wallet_refunded(wallet, expected_value, timeout=60):
    t = time.time()
    while t + timeout > time.time():
        tft_amount = get_wallet_balance(wallet)
        if expected_value == tft_amount:
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


def create_volume_reservation():
    r = zos.reservation_create()
    nodes = zos.nodes_finder.nodes_search()
    node = random.choice(nodes)
    zos.volume.create(r, node.node_id, size=1, type="SSD")
    expiration = j.data.time.epoch + (60 * 5)  # 5 mins
    registered_reservation = zos.reservation_register(r, expiration)
    return registered_reservation


def create_broken_container_reservation():
    """
    create a container with inexistent network_name, should fail
    """
    r = zos.reservation_create()
    nodes = zos.nodes_finder.nodes_search()
    node = random.choice(nodes)
    zos.container.create(
        reservation=r,
        node_id=node.node_id,
        network_name="fake",
        ip_address="172.24.1.10",
        flist="https://hub.grid.tf/zaibon/zaibon-ubuntu-ssh-0.0.2.flist",
        entrypoint="/sbin/my_init",
    )
    expiration = j.data.time.epoch + (60 * 5)  # 5 mins
    registered_reservation = zos.reservation_register(r, expiration)
    return registered_reservation


def test01_reservation_success():
    """
    #. Get wallet 
    #. Create a reservation, should succeed
    #. Make sure you have enough TFT Tokens that cover the reservation amount
    #. User should transfer the amount in TFT, should succeed
    #. Check if the exact amount left the user wallet, should succeed
    #. Check the reservation is Done, State should be "OK"
    """

    # . Get wallet
    wallet = get_funded_wallet()

    # . Create a reservation, should suucced
    registered_reservation = create_volume_reservation()
    assert registered_reservation.reservation_id
    result = get_reservation_result(registered_reservation.reservation_id, timeout=5)
    assert not result, "shouldn't have result before paying"

    # . Make sure you have funds as TFT Tokens that cover the reservation amounts
    user_tft_amount = get_wallet_balance(wallet)
    needed_tft_ammount = amount_paid_to_farmer(registered_reservation)
    assert user_tft_amount > needed_tft_ammount, "Your wallet need to be filled up"

    # . User should transfer the amount in TFT, should succeed
    res = zos.billing.payout_farmers(wallet, registered_reservation)
    assert [t for t in wallet.list_transactions() if res[0] == t.hash], "transaction hash not found"

    # . Check if the exact amount left the user wallet, should succeed
    current_tft_amount = get_wallet_balance(wallet)
    assert "%.2f" % (user_tft_amount - current_tft_amount) == "%.2f" % needed_tft_ammount

    # . Check the reservation is Done, state should be "Ok"
    assert get_reservation_state(registered_reservation.reservation_id) == "Ok", "Nothing deployed"


@pytest.mark.skip(reason="https://github.com/threefoldtech/zos/issues/686")
def test02_reservation_fail():
    """
    #. Get wallet 
    #. Create a broken reservation that will fai later on, reservation state should be "sign"
    #. Make sure you have enough TFT Tokens that cover the reservation amount
    #. User should transfer the  in TFT, should succeed
    #. Check the broken reservation state, should be "ERROR"
    #. Make sure the user got back his TFT, should succeed
    """

    # . Get wallet
    wallet = get_funded_wallet()

    # . Create a broken reservation that will fail later on, reservation state should be "sign"
    registered_reservation = create_broken_container_reservation()
    assert registered_reservation.reservation_id
    result = get_reservation_result(registered_reservation.reservation_id, timeout=5)
    assert not result, "shouldn't have result before paying"

    # . Make sure you have enough TFT Tokens that cover the reservation amount
    user_tft_amount = get_wallet_balance(wallet)
    needed_tft_ammount = amount_paid_to_farmer(registered_reservation)
    assert user_tft_amount > needed_tft_ammount, "Your wallet need to be filled up"

    # . User should transfer the  in TFT, should succeed
    res = zos.billing.payout_farmers(wallet, registered_reservation)
    assert res, "problem during paying"
    assert [t for t in wallet.list_transactions() if res[0] == t.hash], "transaction hash not found"

    # . Check the broken reservation state, should be "Error"
    assert get_reservation_state(registered_reservation.reservation_id) == "ERROR"

    # . Make sure the user got back his TFT, should succeed
    assert check_if_wallet_refunded(wallet, user_tft_amount, timeout=60)


@pytest.mark.skip(reason="https://github.com/threefoldtech/jumpscaleX_libs/issues/156")
def test03_empty_wallet_failed_reservation():
    """
    #. Create new wallet with zero TFT, should succeed
    #. Create a reservation, reservation state should be "pay"
    #. User should pay the farmer, should fail with no enough amount
    """
    # . Create new wallet with zero TFT, should succeed
    wallet = create_new_wallet()

    # . Create a reservation, reservation state should be "pay"
    registered_reservation = create_volume_reservation()
    assert registered_reservation.reservation_id

    # . User should pay the farmer, should fail with no enough amount
    with pytest.raises(Exception):
        # later on can define the exact exception and assert on after issue is solved
        zos.billing.payout_farmers(wallet, registered_reservation)


if __name__ == "__main__":
    if not (WALLET_NAME and WALLET_SECRET):
        raise ValueError("Please provide WALLET_NAME and WALLET_SECRET ")

    pytest.main(["-x", "payment_testing.py"])
