from Jumpscale import j

from .WebdavClient import WebdavClient

JSConfigFactoryBase = j.baseclasses.object_config_collection


class WebdavFactory(JSConfigFactoryBase):
    __jslocation__ = "j.clients.webdav"
    _CHILDCLASS = WebdavClient
