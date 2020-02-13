from Jumpscale import j

from .CarddavClient import CarddavClient

JSConfigFactoryBase = j.baseclasses.object_config_collection


class CarddavFactory(JSConfigFactoryBase):
    # check https://github.com/threefoldtech/jumpscaleX_libs/issues/88
    _CHILDCLASS = CarddavClient
