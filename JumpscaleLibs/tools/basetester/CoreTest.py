from Jumpscale import j


class CoreTest(j.baseclasses.object_config):
    _SCHEMATEXT = """
        @url = jumpscale.bastester.core.1
        name** = ""
        state = "init,running,error,ok"
        
        """

    def run(self):
        """
        to make sure we have the basics working properly
        """
        if self.state != "ok":
            j.data.types.test()
            # self.schema()
            self.bcbd_test()
            j.data.nacl.test()
            self.configobjects()

        self.state = "ok"

    def schema(self):
        j.data.schema.test(name="base")
        j.data.schema.test(name="capnp_schema")
        j.data.schema.test(name="embedded_schema")
        j.data.schema.test(name="lists")
        j.data.schema.test(name="load_data")
        j.data.schema.test(name="numeric")
        j.data.schema.test(name="load_from_dir")
        j.data.schema.test(name="set")
        j.data.schema.test(name="json")
        j.data.schema.test(name="dict")
        j.data.schema.test(name="changed")
        j.data.schema.test(name="enums")

    def bcbd_test(self):
        j.data.bcdb.test_core()

    def configobjects(self):
        j.tutorials.configobjects.test()
        j.tutorials.world.test()
