from Jumpscale import j

from .NodeBaseClass import NodeBaseClass


class NodePacketNet(NodeBaseClass):
    _SCHEMATEXT = """
        @url = jumpscale.bastester.node.packnet.1
        name** = ""
        state = "init,running,error,ok"
        packetnetkey = ""
        packetnetproject = ""
        mother_id** = 0 (I)
        """

    def _init(self, **kwargs):
        self._sshclient = None

    def init(self):
        if self.state != "ok":
            # TODO: deploy packet net machine (fast one) in AMS
            j.shell()
        self.state = "ok"

    @property
    def sshclient(self):
        if not self._sshclient:
            self._sshclient = ...
        return self._sshclient

    def destroy(self):
        # TODO: remove machine
        self.state = "init"


class NodesPacketNet(j.baseclasses.object_config_collection):
    """
    """

    _CHILDCLASS = NodePacketNet
