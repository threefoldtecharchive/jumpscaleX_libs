from Jumpscale import j

from .GoldChainWallet import GoldChainWallet


class GoldChainWalletFactory(j.baseclasses.object_config_collection_testtools):
    """
    Goldchain client object
    """

    _CHILDCLASS = GoldChainWallet
    _name = "wallets"
