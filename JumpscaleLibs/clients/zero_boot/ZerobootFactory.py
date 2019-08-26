import os

from Jumpscale import j

from .ZerobootClient import zero_bootClient

JSConfigFactoryBase = j.baseclasses.object_config_collection


class ZerobootFactory(JSConfigFactoryBase):
    __jslocation__ = "j.clients.zboot"
    _CHILDFACTORY_CLASS = zero_bootClient
