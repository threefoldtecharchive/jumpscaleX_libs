from Jumpscale import j
import gevent


class Ship(j.baseclasses.object_config, j.baseclasses.threebot_actor):
    """
    one ship instance
    """

    _SCHEMATEXT = """
        @url = jumpscale.example.ship.1
        name** = ""
        location = ""
        onsea = true (b)
        """

    def _init(self, **kwargs):
        self.a = "some"
        self.phase1 = False
        self.phase2 = False
        self.phase3 = False

    def wait_test(self, nr):
        gevent.sleep(1)
        print("phase1 :%s" % nr)
        self.phase1 = True
        return nr

    def wait_test2(self, nr):
        gevent.sleep(1)
        assert self.phase1
        print("phase 2:%s" % nr)
        self.phase2 = True
        return nr

    def wait_test3(self, nr):
        gevent.sleep(1)
        assert self.phase2
        print("phase 3:%s" % nr)
        return nr

    def recurring_test(self, nr):
        gevent.sleep(1)
        print("recurring ...")
        # never returns... unless error


class Ships(j.baseclasses.object_config_collection):
    """
    ...
    """

    _CHILDCLASS = Ship

    def _init(self, **kwargs):
        self.a = "a"

    def test(self):
        pass


class WorldTestScheduling(j.baseclasses.testtools, j.baseclasses.object):

    __jslocation__ = "j.tutorials.worldtest.scheduling"

    def test(self):
        """
        to run:

        kosmos -p 'j.tutorials.worldtest.scheduling.test()'
        """

        ships = Ships()
        ships.delete()
        r = ships.find()
        assert r == []

        ship1 = ships.get(name="ibizaboat")
        assert ship1.name == "ibizaboat"

        ship2 = ships.get(name="ibizaboat2")
        assert ship2.name == "ibizaboat2"

        # so we only check every sec
        ship2.scheduler.sleep_time = 1

        nr = 10
        res = {}
        for i in range(nr):
            res[i] = ship2.scheduler.schedule(f"wait_{i}", ship1.wait_test, nr=nr)

        ship2.scheduler.schedule("waitrecurring", ship1.recurring_test, period=2, nr=nr)

        event = ship2.scheduler.event_get("wait_event_1")

        for i in range(nr):
            ship2.scheduler.schedule(f"waitb_{i}", ship1.wait_test2, event=event, nr=nr)

        event2 = ship2.scheduler.event_get("wait_event_2")

        for i in range(nr):
            res[i] = ship2.scheduler.schedule(f"wait_{i}", ship1.wait_test3, event=event2, nr=nr)

        gevent.sleep(1)

        j.shell()

        print("TEST OK")
