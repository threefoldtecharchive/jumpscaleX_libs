from Jumpscale import j


class SmtpdFactory(j.baseclasses.object, j.baseclasses.testtools):

    __jslocation__ = "j.servers.smtp"

    def start(self, address="0.0.0.0", port=7002):
        """
        called when the 3bot starts
        :return:
        """
        self.get_instance(address, port).start()

    def get_instance(self, address="0.0.0.0", port=7002):
        from .app import MailServer
        server = MailServer((address, port))
        return server

    def test(self, name=""):
        self.start()
        print(name)
        self._test_run(name=name)
        self._log_info("All TESTS DONE")
        return "OK"
