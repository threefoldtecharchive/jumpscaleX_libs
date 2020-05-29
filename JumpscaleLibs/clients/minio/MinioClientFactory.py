from Jumpscale import j
from .MinioClient import MinioClient

JSConfigs = j.baseclasses.object_config_collection


class StellarFactory(JSConfigs):
    __jslocation__ = "j.clients.minio"
    _CHILDCLASS = MinioClient
