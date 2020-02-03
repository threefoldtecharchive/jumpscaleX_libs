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
import time

JSConfigClient = j.baseclasses.object_config

_HORIZON_NETWORKS = {"TEST": "https://horizon-testnet.stellar.org", "STD": "https://horizon.stellar.org"}
_NETWORK_PASSPHRASES = {"TEST": Network.TESTNET_NETWORK_PASSPHRASE, "STD": Network.PUBLIC_NETWORK_PASSPHRASE}


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
        if self.secret == "":
            kp = self.create_keypair()
            self.secret = kp.secret
        else:
            kp = Keypair.from_secret(self.secret)
        self.address = kp.public_key


    def create_keypair(self):
        kp = Keypair.random()
        return kp

    def get_balance(self):
        """Gets balance for address
        """
        address = Address(address=self.address)
        address.get()
        self._log_info("Balances: {}".format(address.balances))
        return address.balances

    def activate_through_friendbot(self):
        """Activates and funds a testnet account using riendbot
        """
        if str(self.network) != "TEST":
            raise Exception("Account activation through friendbot is only available on testnet")

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
        transaction = (
            TransactionBuilder(
                source_account=source_account, network_passphrase=_NETWORK_PASSPHRASES[str(self.network)], base_fee=100
            )
            .append_create_account_op(destination=destination_address, starting_balance=starting_balance)
            .build()
        )
        transaction.sign(source)
        try:
            response = server.submit_transaction(transaction)
            self._log_info("Transaction hash: {}".format(response["hash"]))
            self._log_info(response)
        except BadRequestError as e:
            self.log_debug(e)

    def add_trustline(self, asset_code, issuer, secret=None):
        """Create a trustline between you and the issuer of an asset.
        :param asset_code: code which form the asset. For example: 'BTC', 'XRP', ...
        :type asset_code: str
        :param issuer: address of the asset issuer.
        :type issuer: str
        """
        self._change_trustline(asset_code, issuer, secret=secret)

    def delete_trustline(self, asset_code, issuer, secret=None):
        """Deletes a trustline
        :param asset_code: code which form the asset. For example: 'BTC', 'XRP', ...
        :type asset_code: str
        :param issuer: address of the asset issuer.
        :type issuer: str
        """
        self._change_trustline(asset_code, issuer, limit="0", secret=secret)

    def _change_trustline(self, asset_code, issuer, limit=None, secret=None):
        """Create a trustline between you and the issuer of an asset.
        :param asset_code: code which form the asset. For example: 'BTC', 'XRP', ...
        :type asset_code: str
        :param issuer: address of the asset issuer.
        :type issuer: str
        :param limit: The limit for the asset, defaults to max int64(922337203685.4775807). If the limit is set to “0” it deletes the trustline
        """
        # if no secret is provided we assume we change trustlines for this account
        if secret is None:
            secret = self.secret

        server = Server(horizon_url=_HORIZON_NETWORKS[str(self.network)])
        source_keypair = Keypair.from_secret(secret)
        source_public_key = source_keypair.public_key
        source_account = server.load_account(source_public_key)

        base_fee = server.fetch_base_fee()

        transaction = (
            TransactionBuilder(
                source_account=source_account,
                network_passphrase=_NETWORK_PASSPHRASES[str(self.network)],
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
            raise e

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

        self._log_info(destination_address)

        server = Server(horizon_url=_HORIZON_NETWORKS[str(self.network)])
        source_keypair = Keypair.from_secret(self.secret)
        source_public_key = source_keypair.public_key
        source_account = server.load_account(source_public_key)

        base_fee = server.fetch_base_fee()

        issuer = None

        if asset != "XLM":
            assetStr = asset.split(":")
            if len(assetStr) != 2:
                raise Exception("Wrong asset format")
            asset = assetStr[0]
            issuer = assetStr[1]

        transaction = (
            TransactionBuilder(
                source_account=source_account,
                network_passphrase=_NETWORK_PASSPHRASES[str(self.network)],
                base_fee=base_fee,
            )
            .append_payment_op(
                destination=destination_address, amount=str(amount), asset_code=asset, asset_issuer=issuer
            )
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

    def create_preauth_transaction(self, escrow_kp):
        unlock_time = int(time.time())+60*10 # 10 minutes from now
        server = Server(horizon_url=_HORIZON_NETWORKS[str(self.network)])
        escrow_account = server.load_account(escrow_kp.public_key)
        escrow_account.increment_sequence_number()
        tx = TransactionBuilder(escrow_account).append_set_options_op(
            master_weight=0,
            low_threshold=1,
            med_threshold=1,
            high_threshold=1).add_time_bounds(
            unlock_time,
            0).build()
        tx.sign(escrow_kp)
        return tx

    def set_account_signers(self, address, public_key_signer, preauth_tx_hash, signer_kp):
        server = Server(horizon_url=_HORIZON_NETWORKS[str(self.network)])
        account = server.load_account(address)
        tx = TransactionBuilder(account).append_pre_auth_tx_signer(
            preauth_tx_hash,
            1).append_ed25519_public_key_signer(
            public_key_signer,
            1).append_set_options_op(master_weight=1,low_threshold=2,med_threshold=2,high_threshold=2).build()

        tx.sign(signer_kp)
        response=server.submit_transaction(tx)
        self._log_info(response)
        self._log_info('Set the signers of {address} to {pk_signer} and {preauth_hash_signer}'.format(
            address=address,
            pk_signer=public_key_signer,
            preauth_hash_signer=preauth_tx_hash))


    def send_locked_funds(self, destination_address, amount, asset):
        from_kp = Keypair.from_secret(self.secret)
        issuer = None
        asset_code = ""

        if asset != "XLM":
            assetStr = asset.split(":")
            if len(assetStr) != 2:
                raise Exception("Wrong asset format")
            asset_code = assetStr[0]
            issuer = assetStr[1]

        self._log_info('Sending {amount} {asset_code} from {from_address} to {destination_address}'.format(amount=amount, asset_code=asset_code, from_address=from_kp.public_key, destination_address=destination_address))

        self._log_info('Creating escrow account')
        escrow_kp = self.create_keypair()

        # minimum account balance as described at https://www.stellar.org/developers/guides/concepts/fees.html#minimum-account-balance
        server = Server(horizon_url=_HORIZON_NETWORKS[str(self.network)])
        base_fee = server.fetch_base_fee()
        base_reserve = 0.5
        minimum_account_balance = (2+1+3)*base_reserve  # 1 trustline and 3 signers
        required_XLM = minimum_account_balance+base_fee*0.0000001*3

        try:
            self._log_info('Activating escrow account')
            self.activate_account(escrow_kp.public_key, starting_balance=str(math.ceil(required_XLM)))
        except Exception as e:
            self._log_debug(e)

        try:
            self._log_info('Adding trustline to escrow account')
            self.add_trustline(asset_code, issuer, escrow_kp.secret)
        except Exception as e:
            self._log_debug(e)

        try:
            preauth_tx = self.create_preauth_transaction(escrow_kp)
            preauth_tx_hash= preauth_tx.hash()
            self.set_account_signers(escrow_kp.public_key, destination_address, preauth_tx_hash, escrow_kp)
            self._log_info('Unlock Transaction:')
            self._log_info(preauth_tx.to_xdr())
        except Exception as e:
            self._log_debug(e)

        return self.transfer(destination_address=escrow_kp.public_key, amount=amount, asset=asset)
