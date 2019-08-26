from Jumpscale import j
from .MongoEngineClient import MongoEngineClient

JSConfigs = j.baseclasses.object_config_collection


class MongoEngineFactory(JSConfigs):
    __jslocation__ = "j.clients.mongoengine"
    _CHILDFACTORY_CLASS = MongoEngineClient

    def _init(self, **kwargs):
        self.__imports__ = "mongoengine"
