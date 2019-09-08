from Jumpscale import j

try:
    from telegram.ext import Updater, CommandHandler
except:
    j.builders.runtimes.python3.pip_package_install("python-telegram-bot", reset=True)
    from telegram.ext import Updater, CommandHandler

JSConfigClient = j.baseclasses.object_config


class TelegramBot(JSConfigClient):
    """
    You can use this client to run your telegram bots and use Jumpscale config manager
    it exposes updater, bot and and dispatcher to be used by your bot
    """

    _SCHEMATEXT = """
    @url = jumpscale.telegramBot.client
    name** = "" (S)
    bot_token_ = "" (S)
    """

    def _init(self, **kwargs):
        self._updater = None
        self._bot = None
        self._dispatcher = None
        self._command_handler = None

    @property
    def updater(self):
        if not self._updater:
            self._updater = Updater(token=self.bot_token_, use_context=True)

        return self._updater

    @property
    def bot(self):
        if not self._bot:
            self._bot = self.updater.bot

        return self._bot

    @property
    def dispatcher(self):
        if not self._dispatcher:
            self._dispatcher = self.updater.dispatcher

        return self._dispatcher

    def command_register(self, name, command):
        self.dispatcher.add_handler(CommandHandler(name, command))

    def start_polling(self):
        self.updater.start_polling()
