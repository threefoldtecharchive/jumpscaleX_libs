"""
Stellar Client
"""

from Jumpscale import j
try:
    from stellar_sdk import Server, Keypair, TransactionBuilder, Network
    from stellar_sdk.exceptions import BadRequestError
except (ModuleNotFoundError, ImportError):
    j.builders.runtime.python3.pip_package_install("stellar_sdk")

try:
    from stellar_base import Address
except (ModuleNotFoundError, ImportError):
    j.builders.runtime.python3.pip_package_install("stellar_base")

from stellar_sdk import Server, Keypair, TransactionBuilder, Network
from stellar_sdk.exceptions import BadRequestError
from stellar_base import Address

import requests

JSConfigClient = j.baseclasses.object_config

_HORIZON_NETWORKS = {
    "TEST": "https://horizon-testnet.stellar.org",
    "STD": "https://horizon.stellar.org",
}

class StellarClient(JSConfigClient):
    """
    Stellar client object
    """

    _SCHEMATEXT = """
        @url = jumpscale.stellar.client
        name** = "" (S)
        network** = "STD,TEST" (E)
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
        if str(self.network) != "TEST":
            return Exception("You can only fund your account when connected to testnet")

        try:
            res = requests.get("https://friendbot.stellar.org/?addr=" + self.address)
            res.raise_for_status()
            print("account with address: {} funded through friendbot!".format(self.address))
        except requests.exceptions.HTTPError:
            print(res.json())

    def activate_account(self, destination_address, starting_balance="12.50"):
        """Activates another address
        :param destination_address: address of the destination.
        :type destination_address: str
        :param starting_balance: the balance that the destination address will start with. Must be a positive integer expressed as a string. If an empty string is provided, 12,5 XLM will be the starting balance
        :type assetcode: str
        """
        server = Server(horizon_url=_HORIZON_NETWORKS[str(self.network)])
        source = Keypair.from_secret(self.secret)

        source_account = server.load_account(account_id=source.public_key)
        transaction = TransactionBuilder(
            source_account=source_account,
            network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
            base_fee=100) \
            .append_create_account_op(destination=destination_address, starting_balance=starting_balance) \
            .build()
        transaction.sign(source)
        try:
            response = server.submit_transaction(transaction)
            print("Transaction hash: {}".format(response["hash"]))
            print(response)
        except BadRequestError as e:
            print(e)

    def create_trustline(self, issueraddress, assetcode, limit):
        """Create a trustline between you and the issuer of an asset.
        :param issueraddress: address of the asset issuer.
        :type issueraddress: str
        :param assetcode: code which form the asset. For example: 'BTC', 'XRP', ...
        :type assetcode: str
        :param limit: The trust limit parameter limits the number of tokens the distribution account will be able to hold at once. It
        is recommended to either make this number larger than the total number of tokens expected
        to be available on the network or set it to be the maximum value (a total of max int64 stroops) that an account can hold. Expressed as a string.
        :type limit: str
        """
        server = Server(horizon_url=_HORIZON_NETWORKS[str(self.network)])
        source_keypair = Keypair.from_secret(self.secret)
        source_public_key = source_keypair.public_key
        source_account = server.load_account(source_public_key)

        base_fee = server.fetch_base_fee()

        transaction = (
            TransactionBuilder(
                source_account=source_account,
                network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
                base_fee=base_fee,
            )
                .append_change_trust_op(asset_issuer=issueraddress, limit=limit, asset_code=assetcode)
                .set_timeout(30)
                .build()
        )

        transaction.sign(source_keypair)

        try:
            response = server.submit_transaction(transaction)
            print("Transaction hash: {}".format(response["hash"]))
            print(response)
        except BadRequestError as e:
            print(e)


    def transfer(self, destination_address, amount, asset="XLM"):
        """Transfer assets to another address
        :param destination_address: address of the destination.
        :type destination_address: str
        :param amount: amount, can be a floating point number with 7 numbers after the decimal point expressed as a string.
        :type amount: str
        :param asset: asset, asset to transfer (if none is specified the default 'XLM' is used),
        if you wish to specify an asset it should be in format 'assetcode:issuer'. Where issuer is the address of the
        issuer of said asset.
        :type asset: str
        """
        server = Server(horizon_url=_HORIZON_NETWORKS[str(self.network)])
        source_keypair = Keypair.from_secret(self.secret)
        source_public_key = source_keypair.public_key
        source_account = server.load_account(source_public_key)

        base_fee = server.fetch_base_fee()

        issuer = None

        if asset != "XLM":
            assetStr = asset.split(':')
            if len(assetStr) != 2:
                return Exception('Wrong asset format')
            asset = assetStr[0]
            issuer = assetStr[1]

        transaction = (
            TransactionBuilder(
                source_account=source_account,
                network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
                base_fee=base_fee,
            )
                .append_payment_op(destination=destination_address, amount=str(amount), asset_code=asset, asset_issuer=issuer)
                .set_timeout(30)
                .build()
        )

        transaction.sign(source_keypair)

        try:
            response = server.submit_transaction(transaction)
            print("Transaction hash: {}".format(response["hash"]))
            print(response)
        except BadRequestError as e:
            print(e)