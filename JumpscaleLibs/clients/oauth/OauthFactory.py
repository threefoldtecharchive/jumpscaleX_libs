import os
from Jumpscale import j
from .OauthInstance import OauthClient

JSConfigs = j.baseclasses.object_config_collection


class OauthFactory(JSConfigs):
    __jslocation__ = "j.clients.oauth"
    _CHILDCLASS = OauthClient
