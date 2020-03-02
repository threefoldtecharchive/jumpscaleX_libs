from Jumpscale import j

from .CoreTest import CoreTest
from .NodesPacketNet import NodesPacketNet


class Nodes(j.baseclasses.factory_data):

    _CHILDCLASSES = [NodesPacketNet]
    _SCHEMATEXT = """
        @url = jumpscale.example.world2
        name** = "" (S)
        color = "red,blue" (E)
        """


class BaseTesterFactory(j.baseclasses.factory):

    __jslocation__ = "j.tools.basetester"

    _CHILDCLASSES = [Nodes]

    def _init(self, **kwargs):
        self.core = CoreTest(name="core")
        self._node_main = None

    def node_packetnet_init(self, packetnetkey, packetnetproject):
        """
        will initialize the main node which will be used for our tests
        """
        node = self.nodes.nodespacketnet.get(name="main", packetnetkey=packetnetkey, packetnetproject=packetnetproject)

    @property
    def node_main(self):
        if not self._node_main:
            if self.nodespacketnet.find() > 0:
                self._node_main = self.nodespacketnet.get("main")
            if not self._node_main:
                raise j.exceptions.Input("please init packetnet node or digital ocean")
        return self._node_main

    def run(self):
        """
        the main function to run all tests

        kosmos 'j.tools.basetester.run()'

        """
        self.core.run()
        self.node_main.run()
