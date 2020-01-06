from unittest import TestCase

from Jumpscale import j
from parameterized import parameterized


class CoreTests(TestCase):
    @parameterized.expand(["j.tutorials.world.test()", "j.tutorials.world2.test()", "j.tutorials.configobjects.test()"])
    def test(self, cmd):
        eval(cmd)
