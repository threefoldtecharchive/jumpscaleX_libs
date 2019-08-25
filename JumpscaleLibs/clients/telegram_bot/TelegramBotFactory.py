from Jumpscale import j
from .TelegramBotClient import TelegramBot

JSConfigs = j.baseclasses.factory


class TelegramBotFactory(JSConfigs):
    __jslocation__ = "j.clients.telegram_bot"
    _CHILDCLASS = TelegramBot
