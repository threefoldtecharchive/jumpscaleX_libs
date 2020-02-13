from Jumpscale import j

from .S3Client import S3Client

JSConfigBase = j.baseclasses.object_config_collection
skip = j.baseclasses.testtools._skip


class S3Factory(JSConfigBase):
    """
    """

    __jslocation__ = "j.clients.s3"
    _CHILDCLASS = S3Client

    def _init(self, **kwargs):
        self.__imports__ = "minio"

    def install(self):
        p = j.tools.prefab.local
        p.runtimes.pip.install("minio")

    @skip("https://github.com/threefoldtech/jumpscaleX_libs/issues/82")
    def test(self):
        """
        do:
        kosmos 'j.clients.s3.test()'
        """

        client = self.get(name="test")
        self._log_debug(client.serversGet())
