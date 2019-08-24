import os
from Jumpscale import j
from .OauthInstance import OauthClient

JSConfigs = j.baseclasses.objects_config_bcdb


class OauthFactory(JSConfigs):
    __jslocation__ = "j.clients.oauth"
    _CHILDCLASS = OauthClient
