from Jumpscale import j

from .SimpleMailServer import SimpleMailServer


class SimpleMailServerFactory(j.baseclasses.object_config_collection):

    __jslocation__ = "j.servers.simplemail"

    _CHILDCLASS = SimpleMailServer

    def test(self):
        pass
