import os
from Jumpscale import j
from .OauthInstance import OauthClient

JSConfigs = j.baseclasses.factory


class OauthFactory(JSConfigs):
    __jslocation__ = "j.clients.oauth"
    _CHILDCLASS = OauthClient
