from Jumpscale import j

from .WebdavClient import WebdavClient

JSConfigFactoryBase = j.baseclasses.object_config_collection


class WebdavFactory(JSConfigFactoryBase):
    # check https://github.com/threefoldtech/jumpscaleX_libs/issues/94
    _CHILDCLASS = WebdavClient
