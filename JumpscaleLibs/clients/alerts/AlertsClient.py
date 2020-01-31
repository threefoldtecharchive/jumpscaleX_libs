import time

from Jumpscale import j
from Jumpscale.tools.alerthandler.RedisAlertHandler import AlertHandler


class AlertsClient(AlertHandler, j.baseclasses.object_config):

    _SCHEMATEXT = """
        @url = jumpscale.clients.alerts.1
        name** = ""
        redis_addr = "127.0.0.1" (ipaddr)
        redis_port = 6379 (ipport)
        redis_secret = ""
        """

    def _init(self, **kwargs):
        super()._init(**kwargs)

        self._redis_client = None
        self.db = self.redis_client

    @property
    def redis_client(self):
        if self._redis_client is None:
            self._redis_client = j.clients.redis.get(
                addr=self.redis_addr, port=self.redis_port, secret=self.redis_secret
            )

        return self._redis_client
