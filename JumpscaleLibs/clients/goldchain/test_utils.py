from Jumpscale import j


def cleanup(client_name):
    if not  j.clients.goldchain.exists(client_name):
        return

    c = j.clients.goldchain.get(client_name)
    c.wallets.delete() # explicitly delete the children wallets, js' recursive deletion is unstable
    c.delete()