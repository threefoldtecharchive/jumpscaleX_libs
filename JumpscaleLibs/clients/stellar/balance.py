class Balance(object):

    def __init__(self, balance =0.0, asset_code='XLM', asset_issuer=None):
        self.balance = balance
        self.asset_code=asset_code
        self.asset_issuer=asset_issuer
    
    @staticmethod
    def from_horizon_response(response_balance):
        balance=response_balance['balance']
        if response_balance['asset_type']=='native':
            asset_code='XLM'
            asset_issuer=None
        else:
            asset_code=response_balance['asset_code']
            asset_issuer=response_balance['asset_issuer']
        return Balance(balance,asset_code,asset_issuer)

    def __str__(self):
        return "{}".format(self.balance)
    
    def __repr__(self):
        return "{} {} ({})".format(self.balance,self.asset_code,self.asset_issuer)
