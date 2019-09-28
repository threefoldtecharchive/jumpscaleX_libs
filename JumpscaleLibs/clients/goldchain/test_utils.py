from Jumpscale import j

from JumpscaleLibs.clients.goldchain.stub.ExplorerClientStub import GoldChainExplorerGetClientStub


def cleanup(client_name):
    if not  j.clients.goldchain.exists(client_name):
        return

    explorer_client = GoldChainExplorerGetClientStub()
    c = j.clients.goldchain.get(client_name)
    # override internal functionality, as to use our stub client
    c._explorer_get = explorer_client.explorer_get
    c._explorer_post = explorer_client.explorer_post

    c.wallets.delete() # explicitly delete the children wallets, js' recursive deletion is unstable
    c.delete()
