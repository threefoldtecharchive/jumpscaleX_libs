from unittest import TestCase

from parameterized import parameterized

from Jumpscale import j


class CoreTests(TestCase):
    @parameterized.expand(
        [
            "j.tutorials.world.test()",
            "j.tutorials.world2.test()",
            "j.tutorials.configobjects.test()",
            "j.tools.timer.test()",
            "j.data.dict.editor.test()",
            "j.clients.github.test()",
            "j.clients.logger.test()",
            "j.servers.smtp.test()",
            "j.clients.coredns.test()",
            "j.clients.digitalocean.test()",
        ]
    )
    def test(self, cmd):
        eval(cmd)
