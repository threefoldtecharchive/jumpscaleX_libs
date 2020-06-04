from Jumpscale import j
from .MinioHealingClient import MinioHealingClient

JSConfigs = j.baseclasses.object_config_collection


class MinioHealingClientFactory(JSConfigs):
    __jslocation__ = "j.clients.minio"
    _CHILDCLASS = MinioHealingClient
