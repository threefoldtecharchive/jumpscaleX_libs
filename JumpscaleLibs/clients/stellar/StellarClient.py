"""
Stellar Client
"""

from Jumpscale import j
from Jumpscale.clients.http.HttpClient import HTTPError

try:
    from stellar_sdk import (
        Server,
        Keypair,
        TransactionBuilder,
        Network,
        Signer,
        Asset,
        operation,
        Transaction,
        TransactionEnvelope,
    )
    from stellar_sdk.exceptions import BadRequestError
except (ModuleNotFoundError, ImportError):
    j.builders.runtimes.python3.pip_package_install("stellar_sdk")

from stellar_sdk import Server, Keypair, TransactionBuilder, Network, TransactionEnvelope, strkey
from stellar_sdk.exceptions import BadRequestError
from urllib import parse
import time
import decimal
import math
import base64
from .balance import Balance, EscrowAccount, AccountBalances
from .transaction import TransactionSummary, Effect

JSConfigClient = j.baseclasses.object_config

_UNLOCKHASH_TRANSACTIONS_SERVICES = {"TEST": "testnet.threefold.io"}
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
        preauth_txs = (dict)
        """

    def _init(self, **kwargs):
        if self.secret == "":
            kp = Keypair.random()
            self.secret = kp.secret
        else:
            kp = Keypair.from_secret(self.secret)
        self.address = kp.public_key
        self.preauth_txs = {}
        self._unlock_service_client_ = None

    @property
    def _unlock_service_client(self):
        """
        lazy loading of the unlock service client
        """

        if self._unlock_service_client_ is None:
            try:
                c = j.clients.gedis.new(
                    "unlock_service",
                    host=_UNLOCKHASH_TRANSACTIONS_SERVICES[str(self.network)],
                    port=8901,
                    package_name="threefoldfoundation.unlock_service",
                )
            except Exception:
                c = j.clients.gedis.get("unlock_service")

            self._unlock_service_client_ = c.actors.unlock_service
        return self._unlock_service_client_

    def set_unlock_transaction(self, unlock_transaction):
        """
        Adds a xdr encoded unlocktransaction
        :param unlock_transaction: xdr encoded unlocktransactionaddress of the destination.
        :type destination_address: str
        """
        txe = TransactionEnvelope.from_xdr(unlock_transaction, _NETWORK_PASSPHRASES[str(self.network)])
        tx_hash = txe.hash()
        unlock_hash = strkey.StrKey.encode_pre_auth_tx(tx_hash)

        self._unlock_service_client.create_unlockhash_transaction(unlock_hash=unlock_hash, transaction_xdr=txe.to_xdr())

    def _get_horizon_server(self):
        return Server(horizon_url=_HORIZON_NETWORKS[str(self.network)])

    def _get_free_balances(self, address=None):
        if address is None:
            address = self.address
        balances = AccountBalances(address)
        response = self._get_horizon_server().accounts().account_id(address).call()
        for response_balance in response["balances"]:
            balances.add_balance(Balance.from_horizon_response(response_balance))
        return balances

    def get_balance(self):
        """Gets balance for address
        """
        all_balances = self._get_free_balances()
        for account in self._find_escrow_accounts():
            all_balances.add_escrow_account(account)
        return all_balances

    def _find_escrow_accounts(self):
        escrow_accounts = []
        accounts_endpoint = self._get_horizon_server().accounts()
        accounts_endpoint.signer(self.address)
        old_cursor = "old"
        new_cursor = ""
        while new_cursor != old_cursor:
            old_cursor = new_cursor
            accounts_endpoint.cursor(new_cursor)
            response = accounts_endpoint.call()
            next_link = response["_links"]["next"]["href"]
            next_link_query = parse.urlsplit(next_link).query
            new_cursor = parse.parse_qs(next_link_query)["cursor"][0]
            accounts = response["_embedded"]["records"]
            for account in accounts:
                account_id = account["account_id"]
                if account_id == self.address:
                    continue  # Do not take the receiver's account
                all_signers = account["signers"]
                preauth_signers = [signer["key"] for signer in all_signers if signer["type"] == "preauth_tx"]
                # TODO check the tresholds and signers
                # TODO if we can merge, the amount is unlocked ( if len(preauth_signers))==0
                balances = []
                for response_balance in account["balances"]:
                    balances.append(Balance.from_horizon_response(response_balance))

                escrow_account = EscrowAccount(
                    account_id, preauth_signers, balances, _NETWORK_PASSPHRASES[str(self.network)]
                )
                escrow_accounts.append(escrow_account)
        return escrow_accounts

    def claim_locked_funds(self):
        balances = self.get_balance()
        for locked_account in balances.escrow_accounts:
            if locked_account.can_be_unlocked():
                self._unlock_account(locked_account)

    def _unlock_account(self, escrow_account):
        submitted_unlock_transactions = 0
        for unlockhash in escrow_account.unlockhashes:
            unlockhash_transation = self._unlock_service_client.get_unlockhash_transaction(unlockhash=unlockhash)
            if unlockhash_transation is None:
                return
            self._log_info(unlockhash_transation.transaction_xdr)
            self._get_horizon_server().submit_transaction(unlockhash_transation.transaction_xdr)
            submitted_unlock_transactions += 1

        if submitted_unlock_transactions == len(escrow_account.unlockhashes):
            self._merge_account(escrow_account.address)

    def _merge_account(self, address):
        server = self._get_horizon_server()
        account = server.load_account(address)
        # Increment the sequence number in case the unlock transaction was not processed before the load_account call
        # account.increment_sequence_number()
        balances = self._get_free_balances(address)
        base_fee = server.fetch_base_fee()
        transaction_builder = TransactionBuilder(
            source_account=account, network_passphrase=_NETWORK_PASSPHRASES[str(self.network)], base_fee=base_fee
        )
        for balance in balances.balances:
            if balance.is_native():
                continue
            # Step 1: Transfer custom assets
            transaction_builder.append_payment_op(
                destination=self.address,
                amount=balance.balance,
                asset_code=balance.asset_code,
                asset_issuer=balance.asset_issuer,
            )
            # Step 2: Delete trustlines
            transaction_builder.append_change_trust_op(
                asset_issuer=balance.asset_issuer, asset_code=balance.asset_code, limit="0"
            )
        # Step 3: Merge account
        transaction_builder.append_account_merge_op(self.address)

        transaction_builder.set_timeout(30)
        transaction = transaction_builder.build()
        signer_kp = Keypair.from_secret(self.secret)
        transaction.sign(signer_kp)
        server.submit_transaction(transaction)

    def activate_through_friendbot(self):
        """Activates and funds a testnet account using riendbot
        """
        if str(self.network) != "TEST":
            raise Exception("Account activation through friendbot is only available on testnet")

        try:
            resp = j.clients.http.get_response("https://friendbot.stellar.org/?addr=" + self.address)
            if resp.getcode() == 200:
                self._log_info("account with address: {} funded through friendbot".format(self.address))
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
        server = self._get_horizon_server()
        source = Keypair.from_secret(self.secret)

        source_account = server.load_account(account_id=source.public_key)

        base_fee = server.fetch_base_fee()
        transaction = (
            TransactionBuilder(
                source_account=source_account,
                network_passphrase=_NETWORK_PASSPHRASES[str(self.network)],
                base_fee=base_fee,
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
        """Create a trustline to an asset.
        :param asset_code: code of the asset. For example: 'BTC', 'TFT', ...
        :type asset_code: str
        :param issuer: address of the asset issuer.
        :type issuer: str
        """
        self._change_trustline(asset_code, issuer, secret=secret)

    def delete_trustline(self, asset_code, issuer, secret=None):
        """Deletes a trustline
        :param asset_code: code of the asset. For example: 'BTC', 'XRP', ...
        :type asset_code: str
        :param issuer: address of the asset issuer.
        :type issuer: str
        """
        self._change_trustline(asset_code, issuer, limit="0", secret=secret)

    def _change_trustline(self, asset_code, issuer, limit=None, secret=None):
        """Create a trustline between you and the issuer of an asset.
        :param asset_code: code which form the asset. For example: 'BTC', 'TFT', ...
        :type asset_code: str
        :param issuer: address of the asset issuer.
        :type issuer: str
        :param limit: The limit for the asset, defaults to max int64(922337203685.4775807). If the limit is set to “0” it deletes the trustline
        """
        # if no secret is provided we assume we change trustlines for this account
        if secret is None:
            secret = self.secret

        server = self._get_horizon_server()
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
            .append_change_trust_op(asset_issuer=issuer, asset_code=asset_code, limit=limit)
            .set_timeout(30)
            .build()
        )

        transaction.sign(source_keypair)

        try:
            response = server.submit_transaction(transaction)
            self._log_info("Transaction hash: {}".format(response["hash"]))
        except BadRequestError as e:
            self.log_debug(e)
            raise e

    def transfer(self, destination_address, amount, asset="XLM", locked_until=None, memo_text=None, memo_hash=None):
        """Transfer assets to another address
        :param destination_address: address of the destination.
        :type destination_address: str
        :param amount: amount, can be a floating point number with 7 numbers after the decimal point expressed as a string.
        :type amount: str
        :param asset: asset to transfer (if none is specified the default 'XLM' is used),
        if you wish to specify an asset it should be in format 'assetcode:issuer'. Where issuer is the address of the
        issuer of the asset.
        :type asset: str
        :param locked_until: optional epoch timestamp indicating until when the tokens  should be locked.
        :type locked_until: float
        :param text_memo: optional memo text to add to the transaction, a string encoded using either ASCII or UTF-8, up to 28-bytes long
        :type: Union[str, bytes]
        :param memo_hash: optional memo hash to add to the transaction, A 32 byte hash
        :type: Union[str, bytes]
        """
        issuer = None
        self._log_info("Sending {} {} to {}".format(amount, asset, destination_address))
        if asset != "XLM":
            assetStr = asset.split(":")
            if len(assetStr) != 2:
                raise Exception("Wrong asset format")
            asset = assetStr[0]
            issuer = assetStr[1]

        if locked_until is not None:
            return self._transfer_locked_tokens(destination_address, amount, asset, issuer, locked_until)

        server = self._get_horizon_server()
        source_keypair = Keypair.from_secret(self.secret)
        source_public_key = source_keypair.public_key
        source_account = server.load_account(source_public_key)

        base_fee = server.fetch_base_fee()

        transaction_builder = TransactionBuilder(
            source_account=source_account, network_passphrase=_NETWORK_PASSPHRASES[str(self.network)], base_fee=base_fee
        )
        transaction_builder.append_payment_op(
            destination=destination_address, amount=str(amount), asset_code=asset, asset_issuer=issuer
        )
        transaction_builder.set_timeout(30)
        if memo_text is not None:
            transaction_builder.add_text_memo(memo_text)
        if memo_hash is not None:
            transaction_builder.add_hash_memo(memo_hash)

        transaction = transaction_builder.build()

        transaction.sign(source_keypair)

        try:
            response = server.submit_transaction(transaction)
            tx_hash = response["hash"]
            self._log_info("Transaction hash: {}".format(tx_hash))
            return tx_hash
        except BadRequestError as e:
            self._log_debug(e)
            raise e

    def list_transactions(self, address=None):
        """Get the transactions for an adddres
        :param address: address of the effects.In None, the address of this wallet is taken
        :type address: str
        """
        if address is None:
            address = self.address
        tx_endpoint = self._get_horizon_server().transactions()
        tx_endpoint.for_account(address)
        tx_endpoint.include_failed(False)
        transactions = []
        old_cursor = "old"
        new_cursor = ""
        while old_cursor != new_cursor:
            old_cursor = new_cursor
            tx_endpoint.cursor(new_cursor)
            response = tx_endpoint.call()
            next_link = response["_links"]["next"]["href"]
            next_link_query = parse.urlsplit(next_link).query
            new_cursor = parse.parse_qs(next_link_query)["cursor"][0]
            response_transactions = response["_embedded"]["records"]
            for response_transaction in response_transactions:
                transactions.append(TransactionSummary.from_horizon_response(response_transaction))
        return transactions

    def get_transaction_effects(self, transaction_hash, address=None):
        """Get the effects on an adddressfor a specific transaction
        :param transaction_hash: hash of the transaction
        :type transaction_hash: str
        :param address: address of the effects.In None, the address of this wallet is taken
        :type address: str
        """
        if address is None:
            address = self.address
        effects = []
        endpoint = self._get_horizon_server().effects()
        endpoint.for_transaction(transaction_hash)
        old_cursor = "old"
        new_cursor = ""
        while old_cursor != new_cursor:
            old_cursor = new_cursor
            endpoint.cursor(new_cursor)
            response = endpoint.call()
            next_link = response["_links"]["next"]["href"]
            next_link_query = parse.urlsplit(next_link).query
            new_cursor = parse.parse_qs(next_link_query)["cursor"][0]
            response_effects = response["_embedded"]["records"]
            for response_effect in response_effects:
                if "account" in response_effect and response_effect["account"] == address:
                    effects.append(Effect.from_horizon_response(response_effect))
        return effects

    def _transfer_locked_tokens(self, destination_address, amount, asset_code, asset_issuer, unlock_time):
        """Transfer locked assets to another address
        :param destination_address: address of the destination.
        :type destination_address: str
        :param amount: amount, can be a floating point number with 7 numbers after the decimal point expressed as a string.
        :type amount: str
        :param asset_code: asset to transfer
        :type asset_code: str
        :param asset_issuer: if the asset_code is different from 'XlM', the issuer address
        :type asset_issuer: str
        :param unlock_time: an epoch timestamp indicating when the funds should be unlocked.
        :type unlock_time: float
        """

        from_kp = Keypair.from_secret(self.secret)
        unlock_time = math.ceil(unlock_time)
        self._log_info(
            "Sending {amount} {asset_code} from {from_address} to {destination_address} locked until {unlock_time}".format(
                amount=amount,
                asset_code=asset_code,
                from_address=from_kp.public_key,
                destination_address=destination_address,
                unlock_time=unlock_time,
            )
        )

        self._log_info("Creating escrow account")
        escrow_kp = Keypair.random()

        # minimum account balance as described at https://www.stellar.org/developers/guides/concepts/fees.html#minimum-account-balance
        server = self._get_horizon_server()
        base_fee = server.fetch_base_fee()
        base_reserve = 0.5
        minimum_account_balance = (2 + 1 + 3) * base_reserve  # 1 trustline and 3 signers
        required_XLM = minimum_account_balance + base_fee * 0.0000001 * 3

        self._log_info("Activating escrow account")
        self.activate_account(escrow_kp.public_key, str(math.ceil(required_XLM)))

        if asset_code != "XLM":
            self._log_info("Adding trustline to escrow account")
            self.add_trustline(asset_code, asset_issuer, escrow_kp.secret)

        preauth_tx = self._create_unlock_transaction(escrow_kp, unlock_time)
        preauth_tx_hash = preauth_tx.hash()

        # save the preauth transaction in our unlock service
        unlock_hash = strkey.StrKey.encode_pre_auth_tx(preauth_tx_hash)
        self._unlock_service_client.create_unlockhash_transaction(unlock_hash, preauth_tx.to_xdr())

        self._set_account_signers(escrow_kp.public_key, destination_address, preauth_tx_hash, escrow_kp)
        self._log_info("Unlock Transaction:")
        self._log_info(preauth_tx.to_xdr())

        self.transfer(escrow_kp.public_key, amount, asset_code + ":" + asset_issuer)
        return preauth_tx.to_xdr()

    def _create_unlock_transaction(self, escrow_kp, unlock_time):
        server = self._get_horizon_server()
        escrow_account = server.load_account(escrow_kp.public_key)
        escrow_account.increment_sequence_number()
        tx = (
            TransactionBuilder(escrow_account)
            .append_set_options_op(master_weight=0, low_threshold=1, med_threshold=1, high_threshold=1)
            .add_time_bounds(unlock_time, 0)
            .build()
        )
        tx.sign(escrow_kp)
        return tx

    def _set_account_signers(self, address, public_key_signer, preauth_tx_hash, signer_kp):
        server = self._get_horizon_server()
        account = server.load_account(address)
        tx = (
            TransactionBuilder(account)
            .append_pre_auth_tx_signer(preauth_tx_hash, 1)
            .append_ed25519_public_key_signer(public_key_signer, 1)
            .append_set_options_op(master_weight=1, low_threshold=2, med_threshold=2, high_threshold=2)
            .build()
        )

        tx.sign(signer_kp)
        response = server.submit_transaction(tx)
        self._log_info(response)
        self._log_info(
            "Set the signers of {address} to {pk_signer} and {preauth_hash_signer}".format(
                address=address, pk_signer=public_key_signer, preauth_hash_signer=preauth_tx_hash
            )
        )
