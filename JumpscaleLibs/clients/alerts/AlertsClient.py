import time

from Jumpscale import j


class AlertsClient(j.baseclasses.object_config):

    _SCHEMATEXT = """
        @url = jumpscale.clients.alerts.1
        name** = ""
        redis_addr = "127.0.0.1" (ipaddr)
        redis_port = 6379 (ipport)
        redis_secret = ""
        """

    def _init(self, **kwargs):
        self._redis_client = None
        self._alert_handler = None

    @property
    def redis_client(self):
        if self._redis_client is None:
            self._redis_client = j.clients.redis.get(
                addr=self.redis_addr, port=self.redis_port, secret=self.redis_secret
            )

        return self._redis_client

    @property
    def alert_handler(self):
        """
        get an alert handler object and overrides it's redis connection to be able to connect to a remote server
        """
        if self._alert_handler is None:
            self._alert_handler = j.tools.alerthandler
            self._alert_handler.db = self.redis_client

        return self._alert_handler

    def list(self):
        """
        returns all alerts
        """

        return self.alert_handler.list()

    def get(self, identifier, die=False):
        """
        get alert by identifier
        """
        return self.alert_handler.get(identifier=identifier, die=die)

    def delete(self, identifier):
        """
        deletes an alert by identifier
        """
        return self.alert_handler.delete(identifier=identifier)

    def delete_all(self):
        """
        deletes all alerts
        :return:
        """
        return self.alert_handler.delete_all()

    def find(self, cat="", message=""):
        """
        find alerts with category or message
        :param cat: category
        :param message: message
        :return: list of alerts
        """
        return self.alert_handler.find(cat=cat, message=message)
