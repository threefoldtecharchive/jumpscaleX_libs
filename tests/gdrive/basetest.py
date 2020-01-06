from unittest import TestCase
from uuid import uuid4
from Jumpscale import j
import os

os.chdir(j.core.tools.text_replace("{DIR_BASE}/code/github/threefoldtech/digitalmeX/tests/gdrive"))


class Basetest(TestCase):
    def log(self, msg):
        j.core.tools.log(msg, level=20)

    def random_string(self):
        return str(uuid4())[:10]

    @classmethod
    def setUpClass(cls):
        g_client = j.clients.gdrive.get()
        g_client.credfile = "cred.json"
        g_client.save()
        j.sal.fs.createDir(j.core.tools.text_replace("{DIR_BASE}/var/gdrive/static/doc"))
        j.sal.fs.createDir(j.core.tools.text_replace("{DIR_BASE}/var/gdrive/static/slide"))
        j.sal.fs.createDir(j.core.tools.text_replace("{DIR_BASE}/var/gdrive/static/sheet"))
        j.servers.threebot.start(background=True)
