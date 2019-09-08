from Jumpscale import j


class Ship(j.baseclasses.object_config):
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

    __jslocation__ = "j.tutorials.baseclasses.configobjects"

    def test(self):
        """
        to run:

        kosmos 'j.tutorials.baseclasses.configobjects.test()'
        """

        ships = Ships()

        ship1 = ships.get(name="ibizaboat")
        assert ship1.name == "ibizaboat"

        ship2 = ships.get(name="ibizaboat2")
        assert ship2.name == "ibizaboat2"

        # small test to see that the dataprops are visible
        assert len(ship1._dataprops_names_get()) == 3

        assert ship1.onsea == True
        ship1.onsea = False
        assert ship1.onsea == False

        allchildren = ships._children_recursive_get()
        assert len(allchildren) == 2

        print("TEST OK")
