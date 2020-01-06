from Jumpscale import j
import gevent


class SmtpdFactory(j.baseclasses.object, j.baseclasses.testtools):

    __jslocation__ = "j.servers.smtp"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._running_greenlet = None

    def start(self, address="0.0.0.0", port=7002):
        """
        called when the 3bot starts
        :return:
        """
        if self._running_greenlet:
            raise j.exceptions.Runtime("Server is already running")
        server = self.get_instance(address, port)
        self._running_greenlet = gevent.spawn(server.serve_forever)
        gevent.joinall([self._running_greenlet])

    def stop(self):
        if self._running_greenlet:
            self._running_greenlet.kill()
            self._running_greenlet = None

    def get_instance(self, address="0.0.0.0", port=7002):
        from .app import MailServer

        server = MailServer((address, port))
        return server

    def test(self, name=""):
        try:
            db = j.data.bcdb.get("mails")
        except:
            db = j.data.bcdb.new("mails")

        model = db.models_add(
            j.core.tools.text_replace(
                "{DIR_BASE}/code/github/threefoldtech/jumpscaleX_libs/JumpscaleLibs/servers/mail/models/"
            )
        )
        self.start()
        print(name)
        self._test_run(name=name)
        self._log_info("All TESTS DONE")
        return "OK"
