from Jumpscale import j

from .TFChainWallet import TFChainWallet


class TFChainWalletFactory(j.baseclasses.object_config_collection_testtools):
    """
    Tfchain client object
    """

    _CHILDCLASS = TFChainWallet
    _name = "wallets"
