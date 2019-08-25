from Jumpscale import j
from .Dnsmasq import DNSMasq

JSBASE = j.baseclasses.object


class DnsmasqFactory(JSBASE):
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
