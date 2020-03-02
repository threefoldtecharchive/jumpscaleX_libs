from Jumpscale import j
from .Dnsmasq import DNSMasq

JSBASE = j.baseclasses.object
TESTTOOLS = j.baseclasses.testtools


class DnsmasqFactory(JSBASE, TESTTOOLS):
    """Factory class to deal with Dnsmasq"""

    __jslocation__ = "j.sal.dnsmasq"

    def get(self, path="/etc/dnsmasq"):
        """Get an instance of the Dnsmasq class
        :param path: path of the dnsmasq configuration directory, defaults to /etcd/dnsmasq/
        :type path: string, optional
        :return: Dnsmasq instance
        :rtype: Dnsmasq class
        """
        return DNSMasq(path=path)

    def test(self, name=""):
        """Run tests under tests

        :param name: basename of the file to run, defaults to "".
        :type name: str, optional
        """
        self._tests_run(name=name, die=True)
