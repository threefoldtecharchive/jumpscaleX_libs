from Jumpscale import j
from .handle_mail import serve_forever


class SimpleMailServer(j.baseclasses.object_config):
    _SCHEMATEXT = """
       @url =  jumpscale.simplemail.server.1
       name** = "default" (S)
       address = "0.0.0.0" (S)
       port = 25 (I)
       """

    def _init(self, **kwargs):
        self.simplemail_server = j.servers.startupcmd.get(f"email_{self.name}")

    def _start(self):
        serve_forever(self.address, self.port)

    def start(self):
        cmd_start = f"kosmos -p 'j.servers.simplemail.{self.name}._start()'"
        self.simplemail_server.cmd_start = cmd_start
        self.simplemail_server.start()

    def stop(self):
        self.simplemail_server.stop()
