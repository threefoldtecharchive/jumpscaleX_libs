from stellar_sdk import TransactionEnvelope
import datetime, time

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
    def __init__(self, address, unlockhashes, balances,network_passphrase, known_unlock_Transactions={}):
        self.address = address
        self.unlockhashes = unlockhashes
        self.balances = balances
        self.network_passphrase=network_passphrase
        self.unlock_time=None
        self._set_unlock_conditions(known_unlock_Transactions)

    def _set_unlock_conditions(self,known_unlock_Transactions={}):
        for unlock_hash in self.unlockhashes:
            if unlock_hash in known_unlock_Transactions:
                unlockTransaction_xdr=known_unlock_Transactions[unlock_hash]
                txe=TransactionEnvelope.from_xdr(unlockTransaction_xdr,self.network_passphrase)
                tx= txe.transaction
                if tx.time_bounds is not None:
                    self.unlock_time= tx.time_bounds.min_time
                
    
    def can_be_unlocked(self):
        if len(self.unlockhashes) ==0:
            return True
        if self.unlock_time is not None:
            return time.time() > self.unlock_time
        return False

    def __str__(self):
        if self.unlock_time is not None:
            representation="Escrow account {account_id} locked until {unlock_time:%B %d %Y %H:%M:%S}".format(
            account_id=self.address, unlock_time=datetime.datetime.fromtimestamp( self.unlock_time))
        else:
            if len(self.unlockhashes)==0:
                representation = "Escrow account {account_id} is free to be claimed".format(
                account_id=self.address)
            else:
                representation = "Escrow account {account_id} with unknown unlockhashes {unlockhashes}".format(
                account_id=self.address, unlockhashes=self.unlockhashes)
        for balance in self.balances:
            representation += "\n- {balance} {asset_code} ({asset_issuer})".format(
                balance=balance.balance, asset_code=balance.asset_code, asset_issuer=balance.asset_issuer
            )
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
