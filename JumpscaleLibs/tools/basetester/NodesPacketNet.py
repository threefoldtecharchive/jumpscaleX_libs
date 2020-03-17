from Jumpscale import j

from .NodeBaseClass import NodeBaseClass


class NodePacketNet(NodeBaseClass):
    _SCHEMATEXT = """
        @url = jumpscale.bastester.node.packnet.1
        name** = ""
        state = "init,running,error,ok"
        mother_id** = 0 (I)
        plan="c2.medium.x86"
        os = "ubuntu_18_04"
        sshclient_name = ""
        packetnet_id = ""
        """

    def _init(self, **kwargs):
        self._sshclient = None
        self._device_obj = None
        self._packet = j.clients.packetnet.get(name="default")
        self.init()

    @property
    def device_obj(self):
        if not self._device_obj:
            self._device_obj = self._packet.startDevice(
                self.name, plan=self.plan, os=self.os, sshkey="default", remove=False
            )
        if not self.sshclient_name:
            sshclient_name = "packetnet_%s" % self.name
            sshcl = j.clients.ssh.get(name=sshclient_name, addr=self.ipaddress, port=22)
            self.sshclient_name = sshclient_name
            self.packetnet_id = self._device_obj.id
            j.clients.ssh.get(name=self.sshclient_name)

        return self._device_obj

    @property
    def ipaddress(self):
        for ipaddress in self._device_obj.ip_addresses:
            if ipaddress["public"] == True:
                return ipaddress["address"]
        j.shell()
        raise j.exceptions.Base("can not find ipaddress", data=self)

    def init(self, reset=False):
        if self.state != "ok":
            device = self.device_obj  # will set al
        self.state = "ok"

    @property
    def sshclient(self):
        if not self._sshclient:
            self._sshclient = j.clients.ssh.get(name=self.sshclient_name)
        return self._sshclient

    def delete(self):
        self._packet.removeDevice(self.name)
        self.state = "init"


class NodesPacketNet(j.baseclasses.object_config_collection):
    """
    """

    _CHILDCLASS = NodePacketNet
    _name = "packetnet"
