"""
Stellar Client
"""

from Jumpscale import j
from stellar_sdk.keypair import Keypair
from stellar_base import Address
import requests

JSConfigClient = j.baseclasses.object_config


class StellarClient(JSConfigClient):
    """
    Stellar client object
    """

    _SCHEMATEXT = """
        @url = jumpscale.stellar.client
        name** = "" (S)
        address = (S)
        secret = (S)
        """

    def new_keypair(self):
        """Creates a new Stellar keypair (address and secret)
        """
        kp = Keypair.random()
        self.address = kp.public_key
        self.secret = kp.secret
        print("Key: {}".format(kp.secret))
        print("Address: {}".format(kp.public_key))

    def get_balance(self):
        """Gets balance for address
        """
        address = Address(address=self.address)
        address.get()

        print('Balances: {}'.format(address.balances))

    def fund_account(self):
        """Funds a testnet address
        """
        try:
            res = requests.get("https://friendbot.stellar.org/?addr=" + self.address)
            res.raise_for_status()
            print("account with address: {} funded through friendbot!".format(self.address))
        except requests.exceptions.HTTPError:
            print(res.json())

    def activate_account(destination_address, starting_balance):
        """Activates another address
        """
        server = Server(horizon_url="https://horizon-testnet.stellar.org")
        source = Keypair.from_secret(self.secret)

        source_account = server.load_account(account_id=source.public_key)
        transaction = TransactionBuilder(
            source_account=source_account,
            network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
            base_fee=100) \
            .append_create_account_op(destination=destination_address, starting_balance="12.25") \
            .build()
        transaction.sign(source)
        try:
            response = server.submit_transaction(transaction)
            print("Transaction hash: {}".format(response["hash"]))
            print(response)
        except BadRequestError as e:
            print(e)