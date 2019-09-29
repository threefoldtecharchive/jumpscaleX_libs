from Jumpscale import j

from JumpscaleLibs.clients.tfchain.stub.ExplorerClientStub import TFChainExplorerGetClientStub


def cleanup(client_name):
    if not j.clients.tfchain.exists(client_name):
        return

    explorer_client = TFChainExplorerGetClientStub()
    c = j.clients.tfchain.get(client_name)
    # override internal functionality, as to use our stub client
    c._explorer_get = explorer_client.explorer_get
    c._explorer_post = explorer_client.explorer_post

    c.wallets.delete()  # explicitly delete the children wallets, js' recursive deletion is unstable
    c.delete()
