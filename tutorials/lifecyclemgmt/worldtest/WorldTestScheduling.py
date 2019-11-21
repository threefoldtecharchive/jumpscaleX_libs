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
        pass

    def wait_test(self, nr):
        gevent.sleep(1)
        print("waittest:%s" % nr)
        return nr


class Ships(j.baseclasses.object_config_collection):
    """
    ...
    """

    _CHILDCLASS = Ship

    def _init(self, **kwargs):
        self.a = "a"

    def test(self):
        pass


class BaseClasses_Object_Structure(j.baseclasses.testtools, j.baseclasses.object):

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
            res[i] = ship2.scheduler.schedule("wait", ship1.wait_test, nr=nr)

        ship2.scheduler.schedule("waitrecurring", ship1.wait_test, period=2, nr=nr)

        event = ship2.scheduler.event_get("wait_event_1")

        for i in range(nr):
            ship2.scheduler.schedule("waitb", ship1.wait_test, event=event, nr=nr)

        # TODO: not behaving as it should
        gevent.sleep(1111)

        j.shell()

        print("TEST OK")
