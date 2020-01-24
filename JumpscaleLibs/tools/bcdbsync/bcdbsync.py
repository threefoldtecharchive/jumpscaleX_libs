from Jumpscale import j


class BCDBSync(j.baseclasses.object_config):
    """
    sync local bcdb to slave bcdb instances
    """

    _SCHEMATEXT = """
        @url = jumpscale.bcdbsync.1
        name** = "" (S)
        instance_name = "" (S)
        host = 127.0.0.1 (ipaddr)
        port = 6385 (ipport)
    """

    @property
    def client(self):
        return j.clients.redis.get(ipaddr=self.host, port=self.port)

    @property
    def bcdb(self):
        return j.data.bcdb.get(self.instance_name)

    def _get_data(self, id, schema):
        key = f"{self.bcdb.name}:data:1:{schema._schema_url}"
        data = self.client.hget(key, str(id))
        ddata = j.data.serializers.json.loads(data)
        return schema.new(ddata)

    def _set_data(self, obj, type="data"):
        key = f"{self.bcdb.name}:data:1:{obj._schema.url}"
        self.client.hset(key, str(obj.id), obj._json)

    def _set_schema(self, obj):
        schema = obj._schema
        key = f"{self.bcdb.name}:schemas:{schema.url}"
        self.client.hset(key)

    def sync(self):
        for model in j.data.bcdb.get(self.instance_name).models:
            for obj in model.find():
                j.debug()
                self._redis_set(obj)
