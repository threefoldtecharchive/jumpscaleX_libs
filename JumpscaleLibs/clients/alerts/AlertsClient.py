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
        self.serialize_json = True
        self._rediskey_alerts = "alerts"
        self._rediskey_logs = "logs:%s" % (self._threebot_name)

    @property
    def redis_client(self):
        if self._redis_client is None:
            self._redis_client = j.clients.redis.get(
                addr=self.redis_addr, port=self.redis_port, secret=self.redis_secret
            )

        return self._redis_client

    def walk(self, method, args={}):
        """

        def method(key,errorobj,args):
            return args

        will walk over all alerts, can manipulate or fetch that way

        :param method:
        :return:
        """
        for key in self.redis_client.hkeys(self._rediskey_alerts):
            obj = self.get(key)
            args = method(key, obj, args)
        return args

    def list(self, sort_by=None):
        """
        returns all alerts sorted by and key
        """

        def llist(key, err, args):
            args["res"].append([key, err])
            return args

        args = self.walk(llist, args={"res": []})
        return args["res"]

    def find(self, **kwargs):
        """
        find alerts
        """
        pass

    def get(self, identifier):
        """
        get alert by identifier
        """
        pass

    def delete(self, identifier):
        """
        deletes an alert by identifier
        """
        pass

    def delete_all(self):
        """
        deletes all alerts
        :return:
        """
        pass
