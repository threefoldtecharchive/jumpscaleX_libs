from Jumpscale import j


class Car2(j.baseclasses.object_config):
    """
    one car instance
    """

    _SCHEMATEXT = """
        @url = jumpscale.example.car2.1
        name** = ""
        city = ""
        """

    def _init(self, **kwargs):
        pass


class Cars2(j.baseclasses.object_config_collection):
    """
    collection of cars no test tools
    """

    _CHILDCLASS = Car2


class Ship2(j.baseclasses.object_config):
    """
    one ship instance
    """

    _SCHEMATEXT = """
        @url = jumpscale.example.ship2.1
        name** = ""
        location = ""
        onsea = true (b)
        """

    def _init(self, **kwargs):
        self.a = "some"
        pass


class Ships2(j.baseclasses.object_config_collection):
    """
    ...
    """

    _CHILDCLASS = Ship2

    def _init(self, **kwargs):
        self.a = "a"

    def test(self):
        pass


class World2(j.baseclasses.factory_data):

    _CHILDCLASSES = [Cars2, Ships2]
    _SCHEMATEXT = """
        @url = jumpscale.example.world2
        name** = "" (S)
        color = "red,blue" (E)
        """


class BaseClasses_Object_Structure_2(j.baseclasses.testtools, j.baseclasses.object):

    __jslocation__ = "j.tutorials.world2"

    def test(self):
        """
        to run:

        kosmos -p 'j.tutorials.world2.test()'
        """
        w2 = World2(name="world2")
        w3 = World2(name="world3")
        assert isinstance(w2, j.baseclasses.object)
        assert isinstance(w2, j.baseclasses.object_config)
        # needs to be 0 because is a new obj with other children

        assert len(w3.cars2.find()) == 0

        assert len(w2.cars2.find()) == 0
        car3 = w2.cars2.get("rabbit3")
        car3.save()
        assert car3._id  # cannot be empty

        assert len(w2.cars2.find()) == 1  # then we know that world 2 only has 1 car

        car4 = w3.cars2.get("rabbit4")
        car5 = w3.cars2.get("rabbit5")
        car6 = w3.cars2.get("rabbit6")

        assert len(w3.cars2.find()) == 3
        assert len(w2.cars2.find()) == 1

        # clean up
        w2.delete()
        w3.delete()

        print("TEST OK")
