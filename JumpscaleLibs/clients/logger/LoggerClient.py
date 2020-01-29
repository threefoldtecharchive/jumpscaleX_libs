from Jumpscale import j


class LoggerClient(j.baseclasses.object_config):
    """
    A logging client for logs pushed to redis (using our RedisLogger)
    Can be used to fetch logs from any machine
    """

    _SCHEMATEXT = """
        @url = jumpscale.clients.logger.1
        name** = ""
        redis_addr = "127.0.0.1" (ipaddr)
        redis_port = 6379 (ipport)
        redis_secret = ""
        session = "jumpscale" (S)
        date = (D)
        context = "main" (S)
        log_list_prefix = "logs:" (S)
        logs_max = 100 (I)
        """

    def _init(self, **kwargs):
        self._redis_client = None

    @property
    def redis_client(self):
        if self._redis_client is None:
            self._redis_client = j.clients.redis.get(
                addr=self.redis_addr, port=self.redis_port, secret=self.redis_secret
            )

        return self._redis_client

    @property
    def date_str(self):
        if not self.date:
            return j.data.time.getLocalDateHRForFilesystem()
        else:
            return j.data.time.formatTime(self.date, formatstr="%d-%b-%Y")

    @property
    def location(self):
        return "%s/%s/%s" % (self.session, self.date_str, self.context)

    def tail(self, method=None):
        if not method:
            method = print

        prev_logs = []

        while True:
            try:
                list_key = f"{self.log_list_prefix}{self.location}"
                new_logs = self.redis_client.lrange(list_key, 0, self.logs_max)
                logs_diff = set(new_logs) - set(prev_logs)
                for log in logs_diff:
                    method(log.decode())

                prev_logs = new_logs

            except KeyboardInterrupt:
                break

    def _write_log_to_file(self, filepath, log):
        with open(filepath, "ab") as fp:
            fp.write(bytes(log, "UTF-8"))
            fp.write(b"\n")

    def dump(self, filepath):
        parent_dir = j.sal.fs.getParent(filepath)
        j.sal.fs.createDir(parent_dir)

        def write_log(log):
            self._write_log_to_file(filepath, log)

        self.tail(method=write_log)
