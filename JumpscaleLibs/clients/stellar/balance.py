from stellar_sdk import TransactionEnvelope
import datetime, time
from Jumpscale import j


class Balance(object):
    def __init__(self, balance=0.0, asset_code="XLM", asset_issuer=None):
        self.balance = balance
        self.asset_code = asset_code
        self.asset_issuer = asset_issuer

    @staticmethod
    def from_horizon_response(response_balance):
        balance = response_balance["balance"]
        if response_balance["asset_type"] == "native":
            asset_code = "XLM"
            asset_issuer = None
        else:
            asset_code = response_balance["asset_code"]
            asset_issuer = response_balance["asset_issuer"]
        return Balance(balance, asset_code, asset_issuer)
    
    @property
    def is_native(self):
        return self.asset_code == "XLM" and self.asset_issuer is None

    def __str__(self):
        representation = "{balance} {asset_code}".format(balance=self.balance, asset_code=self.asset_code)
        if self.asset_issuer is not None:
            representation += ":{asset_issuer}".format(asset_issuer=self.asset_issuer)
        return representation

    def __repr__(self):
        return str(self)


class EscrowAccount(object):
    def __init__(self, address, unlockhashes, balances, network_passphrase, _get_unlockhash_transaction):
        self.address = address
        self.unlockhashes = unlockhashes
        self.balances = balances
        self.network_passphrase = network_passphrase
        self._get_unlockhash_transaction = _get_unlockhash_transaction
        self.unlock_time = None
        self._set_unlock_conditions()

    def _set_unlock_conditions(self):
        for unlockhash in self.unlockhashes:
            unlockhash_tx = self._get_unlockhash_transaction(unlockhash=unlockhash)
            if unlockhash_tx is None:
                return

            txe = TransactionEnvelope.from_xdr(unlockhash_tx["transaction_xdr"], self.network_passphrase)
            tx = txe.transaction
            if tx.time_bounds is not None:
                self.unlock_time = tx.time_bounds.min_time

    def can_be_unlocked(self):
        if len(self.unlockhashes) == 0:
            return True
        if self.unlock_time is not None:
            return time.time() > self.unlock_time
        return False

    def __str__(self):
        if self.unlock_time is not None:
            representation = "Locked until {unlock_time:%B %d %Y %H:%M:%S} on escrow account {account_id} ".format(
                account_id=self.address, unlock_time=datetime.datetime.fromtimestamp(self.unlock_time)
            )
        else:
            if len(self.unlockhashes) == 0:
                representation = "Free to be claimed on escrow account {account_id}".format(account_id=self.address)
            else:
                representation = "Escrow account {account_id} with unknown unlockhashes {unlockhashes}".format(
                    account_id=self.address, unlockhashes=self.unlockhashes
                )
        for balance in self.balances:
            representation += "\n- {balance} {asset_code}".format(
                balance=balance.balance, asset_code=balance.asset_code
            )
            if balance.asset_issuer is not None:
                representation += ":{asset_issuer}".format(asset_issuer=balance.asset_issuer)
        return representation

    def __repr__(self):
        return str(self)


class AccountBalances(object):
    def __init__(self, address):
        self.address = address
        self.balances = []
        self.escrow_accounts = []

    def add_balance(self, balance):
        self.balances.append(balance)

    def add_escrow_account(self, account):
        self.escrow_accounts.append(account)

    def __str__(self):
        representation = "Balances"
        for balance in self.balances:
            representation += "\n  " + str(balance)
        if len(self.escrow_accounts) > 0:
            representation += "\nLocked balances:"
            for escrow_account in self.escrow_accounts:
                representation += "\n - {account}".format(account=str(escrow_account))
        return representation

    def __repr__(self):
        return str(self)
