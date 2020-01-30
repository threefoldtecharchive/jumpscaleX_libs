"""
Stellar Client
"""

from Jumpscale import j
from Jumpscale.clients.http.HttpClient import HTTPError

try:
    from stellar_sdk import Server, Keypair, TransactionBuilder, Network
    from stellar_sdk.exceptions import BadRequestError
except (ModuleNotFoundError, ImportError):
    j.builders.runtimes.python3.pip_package_install("stellar_sdk")

try:
    from stellar_base import Address
except (ModuleNotFoundError, ImportError):
    j.builders.runtimes.python3.pip_package_install("stellar_base")

from stellar_sdk import Server, Keypair, TransactionBuilder, Network
from stellar_sdk.exceptions import BadRequestError
from stellar_base import Address

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
    def _init(self, **kwargs):
        if self.secret =='':
            kp = Keypair.random()
            self.secret = kp.secret
        else:
            kp=Keypair.from_secret(self.secret)
        self.address = kp.public_key


    def get_balance(self):
        """Gets balance for address
        """
        address = Address(address=self.address)
        address.get()
        self._log_info('Balances: {}'.format(address.balances))
        return address.balances

    def activate_through_friendbot(self):
        """Activates and funds a testnet account using riendbot
        """
        if str(self.network) != "TEST":
            raise Exception('Account activation through friendbot is only available on testnet')

        try:
            resp = j.clients.http.get_response("https://friendbot.stellar.org/?addr=" + self.address)
            if resp.getcode() == 200:
                self._log_info("account with address: {} funded through friendbot!".format(self.address))
        except HTTPError as e:
            if e.status_code == 400:
                msg = e.msg
                if isinstance(msg, (bytes, bytearray)):
                    msg = msg.decode("utf-8")
                    self._log_debug(msg)

    def activate_account(self, destination_address, starting_balance="12.50"):
        """Activates another account
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
            self._log_info("Transaction hash: {}".format(response["hash"]))
            self._log_info(response)
        except BadRequestError as e:
            self.log_debug(e)

    def add_trustline(self, issuer, asset_code):
        """Create a trustline between you and the issuer of an asset.
        :param issuer: address of the asset issuer.
        :type issuer: str
        :param asset_code: code which form the asset. For example: 'BTC', 'XRP', ...
        :type asset_code: str
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
                .append_change_trust_op(asset_issuer=issuer, asset_code=asset_code)
                .set_timeout(30)
                .build()
        )

        transaction.sign(source_keypair)

        try:
            response = server.submit_transaction(transaction)
            self._log_info("Transaction hash: {}".format(response["hash"]))
            self._log_info(response)
        except BadRequestError as e:
            self.log_debug(e)


    def transfer(self, destination_address, amount, asset="XLM"):
        """Transfer assets to another address
        :param destination_address: address of the destination.
        :type destination_address: str
        :param amount: amount, can be a floating point number with 7 numbers after the decimal point expressed as a string.
        :type amount: str
        :param asset: asset to transfer (if none is specified the default 'XLM' is used),
        if you wish to specify an asset it should be in format 'assetcode:issuer'. Where issuer is the address of the
        issuer of the asset.
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
                raise Exception('Wrong asset format')
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
            self._log_info("Transaction hash: {}".format(response["hash"]))
            self._log_info(response)
        except BadRequestError as e:
            self._log_debug(e)
            raise e