from unittest import TestCase

from gevent.monkey import patch_all
from parameterized import parameterized

from Jumpscale import j

patch_all(subprocess=False)


class CoreTests(TestCase):
    @parameterized.expand(
        [
            "j.tutorials.world.test()",
            "j.tutorials.world2.test()",
            "j.tutorials.configobjects.test()",
            "j.tools.timer.test()",
            "j.clients.github.test()",
            "j.clients.coredns.test()",
            "j.servers.smtp.test()",
        ]
    )
    def test(self, cmd):
        eval(cmd)
