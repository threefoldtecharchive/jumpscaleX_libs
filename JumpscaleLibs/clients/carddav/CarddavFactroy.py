from Jumpscale import j

from .CarddavClient import CarddavClient

JSConfigFactoryBase = j.baseclasses.object_config_collection


class CarddavFactory(JSConfigFactoryBase):
    __jslocation__ = "j.clients.carddav"
    _CHILDCLASS = CarddavClient
