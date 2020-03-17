from Jumpscale import j

from .CoreTest import CoreTest
from .NodesPacketNet import NodesPacketNet


class Nodes(j.baseclasses.factory_data):

    _CHILDCLASSES = [NodesPacketNet]
    _SCHEMATEXT = """
        @url = jumpscale.basetester.nodes
        name** = "" (S)
        sshkey = "default"
        """


class BaseTesterFactory(j.baseclasses.factory):

    __jslocation__ = "j.tools.basetester"

    _CHILDCLASSES = [Nodes]

    def _init(self, **kwargs):
        # self.core = CoreTest(name="core")
        pass

    def node_get(self, name="basetest", plan="c2.medium.x86", os="ubuntu_18_04", delete=False):
        node = self.nodes.packetnet.get(name=name, plan=plan, os=os)
        if delete:
            node.delete()
        return node

    def run(self):
        """
        the main function to run all tests

        kosmos 'j.tools.basetester.run()'

        """
        # self.core.run()
        j.debug()
        n = self.node_get()
