from Jumpscale import j

from .CoreTest import CoreTest
from .NodesPacketNet import NodesPacketNet
from .NodesDigitalOcean import NodesDigitalOcean


class Nodes(j.baseclasses.factory_data):

    _CHILDCLASSES = [NodesPacketNet, NodesDigitalOcean]
    _SCHEMATEXT = """
        @url = jumpscale.basetester.nodes
        name** = "" (S)
        sshkey = "default"
        """


class BaseTesterFactory(j.baseclasses.factory):

    __jslocation__ = "j.tools.basetester"

    _CHILDCLASSES = [Nodes]

    def _init(self, **kwargs):
        pass

    def node_get_packetnet(self, name="basetest", plan="c2.medium.x86", os="ubuntu_18_04", reset=False):
        node = self.nodes.packetnet.get(name=name, plan=plan, os=os)
        node.start(reset=reset)
        return node

    def node_get_digitalocean(self, name="basetest", reset=False):
        node = self.nodes.digitalocean.get(name=name)
        node.start(reset=reset)
        return node

    def coretest(self):
        """
        kosmos 'j.tools.basetester.coretest()'
        """
        self.core = CoreTest(name="core")

    def run(self):
        """
        the main function to run all tests

        kosmos 'j.tools.basetester.run()'

        """
        self.core = CoreTest(name="core")
        n = self.node_get_digitalocean()
