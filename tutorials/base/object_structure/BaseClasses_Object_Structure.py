from Jumpscale import j


class Car(j.baseclasses.object_config):
    """
    one car instance
    """

    _SCHEMATEXT = """
        @url = jumpscale.example.car.1
        name* = ""
        city = ""
        """

    def _init(self, **kwargs):
        pass


class Cars(j.baseclasses.object_config_collection):
    """
    collection of cars no test tools
    """

    _CHILDCLASS = Car


class Ship(j.baseclasses.object_config):
    """
    one ship instance
    """

    _SCHEMATEXT = """
        @url = jumpscale.example.ship.1
        name* = ""
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


class World(j.baseclasses.factory()):
    """
    generic usable factory
    """

    _CHILDCLASSES = [Cars, Ships, Ship]


class WorldWithData(j.baseclasses.factory(isconfig_object=True)):

    _CHILDCLASSES = [Cars, Ships]
    _SCHEMATEXT = """
        @url = jumpscale.example.ship.1
        name* = ""
        color = "red,blue" (E)
        """


class BaseClasses_Object_Structure(j.baseclasses.testtools, j.baseclasses.object):

    __jslocation__ = "j.tutorials.baseclasses.world"

    def test(self):
        """
        to run:

        kosmos 'j.tutorials.baseclasses.world.test()'
        """

        ships = Ships()

        ship1 = ships.get(name="ibizaboat")
        assert ship1.name == "ibizaboat"

        # small test to see that the dataprops are visible
        assert len(ship1._dataprops_names_get()) == 3

        w = World()

        car = w.cars.get("rabbit")
        car2 = w.cars.get("bobby")

        assert car.name == "rabbit"
        w.ship.onsea = False
        assert w.ship.onsea == False

        assert len(w.cars.find()) == 2

        assert len(w.cars.find(name="rabbit")) == 1

        allchildren = w._children_recursive_get()
        assert len(allchildren) == 5

        w.save()

        w.cars._children = j.baseclasses.dict()

        assert len(w.cars._model.find()) == 2  # proves that the data has been saved in the DB

        assert len(w.cars.find()) == 2

        w2 = WorldWithData()
        w3 = WorldWithData()
        assert isinstance(w2, j.baseclasses.factory)
        assert isinstance(w2, j.application.JSConfigsFactory)
        assert isinstance(w2, j.baseclasses.object_config)

        # needs to be 0 because is a new obj with other children

        assert len(w3.cars.find()) == 0

        assert len(w2.cars.find()) == 0
        car3 = w2.cars.get("rabbit3")
        car3.save()
        assert car3._id  # cannot be empty

        assert len(w2.cars.find()) == 1  # then we know that world 2 only has 1 car

        assert len(w.cars.find()) == 2

        car4 = w3.cars.get("rabbit4")
        car5 = w3.cars.get("rabbit5")
        car6 = w3.cars.get("rabbit6")

        assert len(w3.cars.find()) == 3
        assert len(w2.cars.find()) == 1

        print("TEST OK")
