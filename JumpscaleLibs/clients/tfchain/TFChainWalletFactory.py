from Jumpscale import j

from .TFChainWallet import TFChainWallet


class TFChainWalletFactory(j.baseclasses.factory):
    """
    Tfchain client object
    """

    _CHILDCLASS = TFChainWallet
    _name = "wallets"
