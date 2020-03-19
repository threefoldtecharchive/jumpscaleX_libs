from Jumpscale import j
from .CoreXClient import CoreXClient

skip = j.baseclasses.testtools._skip


class CoreXClientFactory(j.baseclasses.object_config_collection_testtools):

    __jslocation__ = "j.clients.corex"
    _CHILDCLASS = CoreXClient

    def _init(self, **kwargs):
        pass

    def test(self):
        """
        kosmos 'j.clients.corex.test()'
        :return:
        """

        def test(passw=False):
            try:
                j.clients.corex.reset()

                s = j.servers.corex.default
                s.port = 8002

                if passw:
                    s.user = "user"
                    s.passwd = "pass"
                    cl = self.get(name="test", addr="localhost", port=s.port, login="user", passwd_="pass")
                else:
                    cl = self.get(name="test", addr="localhost", port=s.port)

                s.start()

                assert cl.process_list() == []

                r = cl.process_start("mc")

                r2 = cl.process_info_get(r["id"])
                assert r["id"] == r2["id"]

                r2 = cl.process_info_get(corex_id=r["id"])
                assert r["id"] == r2["id"]

                r2 = cl.process_info_get(corex_id=r["id"])
                assert r["id"] == r2["id"]

                r2 = cl.process_info_get(pid=r["pid"])

                assert r["id"] == r2["id"]

                cl.ui_link_print(r["id"])

                # lets do the stop test
                cl.process_kill(r["id"])
                r = cl.process_info_get(r["id"])
                assert r["state"] == "stopped"

                r3 = cl.process_start("ls /")
                print(cl.process_log_get(r3["id"]))
                assert r3["status"] == "success"
                r3 = cl.process_info_get(r3["id"])
                assert r3["state"] == "stopped"

                j.clients.corex.reset()
            finally:
                cl.process_clean()

        print("TEST NO AUTH")
        test(False)
        print("TEST WITH AUTH")
        test(True)
        print("ALL TEST OK")
