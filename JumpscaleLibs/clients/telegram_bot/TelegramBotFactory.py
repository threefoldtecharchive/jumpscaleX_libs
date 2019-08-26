from Jumpscale import j
from .TelegramBotClient import TelegramBot

JSConfigs = j.baseclasses.object_config_collection


class TelegramBotFactory(JSConfigs):
    __jslocation__ = "j.clients.telegram_bot"
    _CHILDCLASS = TelegramBot
