from Jumpscale import j

try:
    from mongoengine import connect
except:
    j.builders.runtimes.python3.pip_package_install("mongoengine")
    from mongoengine import connect


JSConfigClient = j.baseclasses.object_config


class MongoEngineClient(JSConfigClient):
    _SCHEMATEXT = """
        @url = jumpscale.MongoEngine.client
        name* = "default" (S)
        host = "localhost" (S)
        port = 27017 (ipport)
        username = "" (S)
        password_ = "" (S)
        alias = "" (S)
        db = "" (S)
        authentication_source = "" (S)
        authentication_mechanism = "" (S)
        ssl = False (B)
        replicaset = "" (S)
        """

    def _init(self, **kwargs):
        kwargs = {}
        connect(**kwargs)
