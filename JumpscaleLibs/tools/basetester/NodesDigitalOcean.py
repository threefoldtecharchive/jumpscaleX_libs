from Jumpscale import j

from .NodeBaseClass import NodeBaseClass


class NodeDigitalOcean(NodeBaseClass):
    _SCHEMATEXT = """
        @url = jumpscale.bastester.node.digitalocean.1
        name** = ""
        state = "delete,init,running,error,ok"
        mother_id** = 0 (I)
        sshclient_name = ""
        image="ubuntu 18.04"
        size_slug="s-2vcpu-4gb"
        """

    def _init(self, **kwargs):
        self._sshclient = None
        self._device_obj = None
        self._client = j.clients.digitalocean.get(name="default")

    @property
    def device_obj(self):
        if not self._device_obj:
            self.start()
        return self._device_obj

    @property
    def ipaddress(self):
        j.shell()

    def start(self, reset=False):
        self._droplet, self._sshclient = self._client.droplet_create(
            name=self.name, sshkey=None, region="ams3", image=self.image, size_slug=self.size_slug, delete=reset
        )
        self.sshclient_name = self._sshclient.name
        return self.sshclient

    def init(self, reset=False):
        if self.state != "ok" or reset:
            self.start(reset=reset)
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


class NodesDigitalOcean(j.baseclasses.object_config_collection):
    """
    """

    _CHILDCLASS = NodeDigitalOcean
    _name = "digitalocean"
