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

    __jslocation__ = "j.tutorials.configobjects"

    def test(self):
        """
        to run:

        kosmos -p 'j.tutorials.baseclasses.configobjects.test()'
        """

        ships = Ships()
        ships.delete()
        r = ships.find()
        assert r == []

        ship1 = ships.get(name="ibizaboat")
        assert ship1.name == "ibizaboat"

        ship2 = ships.get(name="ibizaboat2")
        assert ship2.name == "ibizaboat2"

        # small test to see that the dataprops are visible
        assert len(ship1._dataprops_names_get()) == 3

        assert ship1._autosave == True
        # will not save yet because its the default == True and does not change
        assert ship1.onsea == True
        ship1.onsea = False
        # now a change will happen
        assert ship1.onsea == False

        allchildren = ships._children_recursive_get()
        assert len(allchildren) == 2

        names = ships._children_names_get("i")
        assert len(names) == 2
        names = ships._children_names_get("ibiza")
        assert len(names) == 2
        names = ships._children_names_get("ibizq")
        assert len(names) == 0

        assert ships.exists(name="ibizaboat2")

        assert ships.ibizaboat2 == ship2

        print("TEST OK")
