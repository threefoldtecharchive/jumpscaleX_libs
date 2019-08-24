from Jumpscale import j

from .TFChainWallet import TFChainWallet


class TFChainWalletFactory(j.baseclasses.objects_config_bcdb):
    """
    Tfchain client object
    """

    _CHILDCLASS = TFChainWallet
    _name = "wallets"
