from Jumpscale import j
from collections import namedtuple
from .asimap.server import Server
import os

TESTTOOLS = j.baseclasses.testtools


class ImapServer(j.baseclasses.factory, TESTTOOLS):
    __jslocation__ = "j.servers.imap"

    def start(self, address="0.0.0.0", port=7143):
        self.get_instance(address, port).serve_forever()

    def get_instance(self, address, port):
        models = self.get_models()
        return Server(address, port, models).server

    def get_models(self):
        try:
            bcdb = j.data.bcdb.get(name="mails")
        except j.exceptions.Input:
            bcdb = j.data.bcdb.new(name="mails")

        models = os.path.join(self._dirpath, "..", "models")
        bcdb.models_add(models)
        folder_model = bcdb.model_get(url="jumpscale.email.folder")
        if not folder_model.find(name="inbox"):
            folder = folder_model.new()
            folder.name = "inbox"
            folder.subscribed = True
            folder.save()

        message_model = bcdb.model_get(url="jumpscale.email.message")
        Models = namedtuple("Models", "message folder")
        models = Models(message_model, folder_model)
        return models

    def test(self, name=""):
        """
        kosmos 'j.servers.imap.test()'

        """
        self._tests_run(name=name)
