import time
import requests
from Jumpscale import j


JSBASE = j.baseclasses.object
DNS_PREFIX = j.core.myenv.config.get("DNS_PREFIX", "")

"""
This module assume having tcprouter and coredns installed.
tfgateway = j.tools.tf_gateway.get(j.core.db) # or another redisclient
tfgateway.tcpservice_register("bing", "www.bing.com", "122.124.214.21")
tfgateway.domain_register_a("ahmed", "bots.grid.tf.", "123.3.23.54")
"""


class TFGateway(j.baseclasses.object):
    """
    tool to register tcpservices in tcprouter and coredns records
    """

    def __init__(self, redisclient, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redisclient = redisclient

    def _validate_ip(self, ip):
        if not j.data.types.ipaddr.check(ip):
            raise j.exceptions.Value("invalid ip {}".format(ip))

    def _records_get(self, record_ip):
        records = []
        if isinstance(record_ip, str):
            self._validate_ip(record_ip)
            records = [{"ip": record_ip}]

        elif isinstance(record_ip, list):
            for ip in record_ip:
                self._validate_ip(ip)
                records.append({"ip": ip})
        return records

    def install(self):
        j.builders.network.tcprouter.install()
        j.builders.network.tcprouter.start()
        j.builders.network.coredns.install()
        j.builders.network.coredns.start()

    ## COREDNS redis backend
    def domain_register(self, name, domain="bots.grid.tf.", record_type="a", records=None, prefix=DNS_PREFIX):
        """registers domain in coredns (needs to be authoritative)

        e.g: ahmed.bots.grid.tf

        requires nameserver on bots.grid.tf (authoritative)
        - ahmed is name
        - domain is bots.grid.tf

        :param name: name
        :type name: str
        :param domain: str, defaults to "bots.grid.tf."
        :type domain: str, optional
        :param record_type: valid dns record (a, aaaa, txt, srv..), defaults to "a"
        :type record_type: str, optional
        :param records: records list, defaults to None
        :type records: [type], optional is [ {"ip":machine ip}] in case of a/aaaa records
        """

        if not domain.endswith("."):
            domain += "."
        data = {}
        records = records or []
        if self.redisclient.hexists(prefix + domain, name):
            data = j.data.serializers.json.loads(self.redisclient.hget(prefix + domain, name))

        if record_type in data:
            for record in data[record_type]:
                if record not in records:
                    records.append(record)
        data[record_type] = records
        self.redisclient.hset(prefix + domain, name, j.data.serializers.json.dumps(data))

    def domain_list(self, prefix=DNS_PREFIX):
        domains = [domain_name[len(prefix):] for domain_name in self.redisclient.keys(DNS_PREFIX + "*.")]
        return domains

    def domain_exists(self, domain, prefix=DNS_PREFIX):
        if not domain.endswith("."):
            domain += "."
        if self.redisclient.exists(prefix + domain):
            return True
        subdomain, domain = domain.split(".", 1)
        return self.redisclient.hexists(prefix + domain, subdomain)

    def domain_dump(self, domain, prefix=DNS_PREFIX):
        if not domain.endswith("."):
            domain += "."
        resulset = {}
        for key, value in self.redisclient.hgetall(prefix + domain).items():
            resulset[key.decode()] = j.data.serializers.json.loads(value)
        return resulset

    def subdomain_get(self, domain, subdomain, prefix=DNS_PREFIX):
        if not domain.endswith("."):
            domain += "."
        subdomain_info = self.redisclient.hget(prefix + domain, subdomain)
        return j.data.serializers.json.loads(subdomain_info)

    def domain_register_a(self, name, domain, record_ip):
        """registers A domain in coredns (needs to be authoritative)

        e.g: ahmed.bots.grid.tf

        requires nameserver on bots.grid.tf (authoritative)
        - ahmed is name
        - domain is bots.grid.tf

        :param name: myhost
        :type name: str
        :param domain: str, defaults to "grid.tf."
        :type domain: str, optional
        :param record_ip: machine ip in ipv4 format
        :type record_ip: str or list of str
        """
        records = self._records_get(record_ip)
        return self.domain_register(name, domain, record_type="a", records=records)

    def domain_register_aaaa(self, name, domain, record_ip):
        """registers A domain in coredns (needs to be authoritative)

        e.g: ahmed.bots.grid.tf

        requires nameserver on bots.grid.tf (authoritative)
        - ahmed is name
        - domain is bots.grid.tf

        :param name: name
        :type name: str
        :param domain: str, defaults to "bots.grid.tf."
        :type domain: str, optional
        :param record_ip: machine ips in ipv6 format
        :type record_ip: list of str
        """
        records = self._records_get(record_ip)
        return self.domain_register(name, domain, record_type="aaaa", records=records)

    def domain_register_cname(self, name, domain, host):
        """Register CNAME record

        :param name: name
        :type name: str
        :param domain: str, defaults to "bots.grid.tf."
        :type domain: str, optional
        :param host: cname
        :type host: str
        """
        if not host.endswith("."):
            host += "."
        self.domain_register(name, domain, "cname", records=[{"host": host}])

    def domain_register_ns(self, name, domain, host):
        """register NS record

        :param name: name
        :type name: str
        :param domain: str, defaults to "bots.grid.tf."
        :type domain: str, optional
        :param host: host
        :type host: str

        """
        self.domain_register(name, domain, "ns", records=[{"host": host}])

    def domain_register_txt(self, name, domain, text):
        """register TXT record

        :param name: name
        :type name: str
        :param domain: str, defaults to "bots.grid.tf."
        :type domain: str, optional
        :param text: text
        :type text: text
        """

        self.domain_register(name, domain, "txt", records=[{"text": text}])

    def domain_register_mx(self, name, domain, host, priority=10):
        """register MX record

        :param name: name
        :type name: str
        :param domain: str, defaults to "bots.grid.tf."
        :type domain: str, optional
        :param host: host for mx e.g mx1.example.com
        :type host: str
        :param priority: priority defaults to 10
        :type priority: int

        """

        self.domain_register(name, domain, "mx", records=[{"host": host, "priority": priority}])

    def domain_register_srv(self, name, domain, host, port, priority=10, weight=100):
        """register SRV record

        :param name: name
        :type name: str
        :param domain: str, defaults to "bots.grid.tf."
        :type domain: str, optional
        :param host: host for mx e.g mx1.example.com
        :type host: str
        :param port: port for srv record
        :type port: int
        :param priority: priority defaults to 10
        :type priority: int
        :param weight: weight defaults to 100
        :type weight: int

        """
        self.domain_register(
            name, domain, "srv", records=[{"host": host, "port": port, "priority": priority, "weight": weight}]
        )

    def domain_unregister(self, name, domain="bots.grid.tf.", record_type="a", prefix=DNS_PREFIX, records=[]):
        """unregisters domain from coredns
        :param name: name
        :type name: str
        :param domain: str, defaults to "bots.grid.tf."
        :type domain: str, optional
        :param record_type: valid dns record (a, aaaa, txt, srv..), defaults to "a"
        :type record_type: str, optional
        :param records: records list, defaults to []
        :type records: [type], optional is [ {"ip":machine ip}] in case of a/aaaa records
        """

        if not domain.endswith("."):
            domain += "."
        domain_key = prefix + domain

        record_data = j.data.serializers.json.loads(self.redisclient.hget(domain_key, name))
        if not record_data:
            return

        type_records = record_data.get(record_type, [])
        if len(type_records) == 0:
            return

        for rec_to_delete in records:
            for i in range(0, len(type_records)):
                if rec_to_delete == type_records[i]:
                    break
            if i < len(type_records):
                type_records.pop(i)

        if len(type_records) == 0:
            record_data.pop(record_type, None)
        else:
            record_data[record_type] = type_records

        if not record_data:
            self.redisclient.hdel(domain_key, name)
        else:
            self.redisclient.hset(domain_key, name, j.data.serializers.json.dumps(record_data))

    def domain_unregister_a(self, name, domain, record_ip):
        """unregisters A domain from coredns

        e.g: ahmed.bots.grid.tf

        - ahmed is name
        - domain is bots.grid.tf

        :param name: myhost
        :type name: str
        :param domain: str, defaults to "grid.tf."
        :type domain: str, optional
        :param record_ip: machine ip in ipv4 format
        :type record_ip: str or list of str
        """

        records = self._records_get(record_ip)
        self.domain_unregister(name, domain, record_type="a", records=records)

    def domain_unregister_aaaa(self, name, domain, record_ip):
        """unregisters A domain from coredns

        e.g: ahmed.bots.grid.tf

        - ahmed is name
        - domain is bots.grid.tf

        :param name: name
        :type name: str
        :param domain: str, defaults to "bots.grid.tf."
        :type domain: str, optional
        :param record_ip: machine ips in ipv6 format
        :type record_ip: list of str
        """

        records = self._records_get(record_ip)
        self.domain_unregister(name, domain, record_type="aaaa", records=records)

    def domain_unregister_cname(self, name, domain, host):
        """unregister CNAME record

        :param name: name
        :type name: str
        :param domain: str, defaults to "bots.grid.tf."
        :type domain: str, optional
        :param host: cname
        :type host: str
        """

        if not host.endswith("."):
            host += "."
        self.domain_unregister(name, domain, record_type="cname", records=[{"host": host}])

    def domain_unregister_ns(self, name, domain, host):
        """unregister NS record

        :param name: name
        :type name: str
        :param domain: str, defaults to "bots.grid.tf."
        :type domain: str, optional
        :param host: host
        :type host: str

        """

        self.domain_unregister(name, domain, record_type="ns", records=[{"host": host}])

    def domain_unregister_txt(self, name, domain, text):
        """unregister TXT record

        :param name: name
        :type name: str
        :param domain: str, defaults to "bots.grid.tf."
        :type domain: str, optional
        :param text: text
        :type text: text
        """

        self.domain_unregister(name, domain, record_type="txt", records=[{"text": text}])

    def domain_unregister_mx(self, name, domain, host, priority=10):
        """unregister MX record

        :param name: name
        :type name: str
        :param domain: str, defaults to "bots.grid.tf."
        :type domain: str, optional
        :param host: host for mx e.g mx1.example.com
        :type host: str
        :param priority: priority defaults to 10
        :type priority: int

        """

        self.domain_unregister(name, domain, record_type="mx", records=[{"host": host, "priority": priority}])

    def domain_unregister_srv(self, name, domain, host, port, priority=10, weight=100):
        """unregister SRV record

        :param name: name
        :type name: str
        :param domain: str, defaults to "bots.grid.tf."
        :type domain: str, optional
        :param host: host for mx e.g mx1.example.com
        :type host: str
        :param port: port for srv record
        :type port: int
        :param priority: priority defaults to 10
        :type priority: int
        :param weight: weight defaults to 100
        :type weight: int

        """

        self.domain_unregister(
            name, domain, "srv", records=[{"host": host, "port": port, "priority": priority, "weight": weight}]
        )

    ## TCP Router redis backend
    def tcpservice_register(self, domain, service_addr="", service_port=443, service_http_port=80, client_secret=""):
        """
        register a tcpservice to be used by tcprouter in j.core.db

        :param domain: (Server Name Indicator SNI) (e.g www.facebook.com)
        :type domain: str
        :param service_addr: IPAddress of the service
        :type service_endpoint: string
        :param service_port: Port of the tls services
        :type service_port: int
        :param service_http_port: Port of the service
        :type service_http_port: int
        """
        if not any([service_addr, client_secret]) or all([service_addr, client_secret]):
            raise j.exceptions.Value(
                f"Need to provide only service_addr (you passed {service_addr}) or client_secret (you passed {client_secret})"
            )
        service = {}
        service["Key"] = "/tcprouter/service/{}".format(domain)
        record = {
            "addr": service_addr,
            "tlsport": service_port,
            "httpport": service_http_port,
            "clientsecret": client_secret,
        }
        json_dumped_record_bytes = j.data.serializers.json.dumps(record).encode()
        b64_record = j.data.serializers.base64.encode(json_dumped_record_bytes).decode()
        service["Value"] = b64_record
        self.redisclient.set(service["Key"], j.data.serializers.json.dumps(service))

    def tcpservice_unregister(self, domain):
        key = "/tcprouter/service/{}".format(domain)
        self.redisclient.delete(key)

    def create_tcprouter_service_client(
        self, name=None, local_ip="127.0.0.1", local_port=80, remote_url=None, remote_port=18000, secret=None
    ):
        """
        helper method to get/start tcprouter client [used to forward the traffic to tcprouter server]
        :param name: client name (str)
        :param local_address: ip of the running server you want to expose (ipaddr)
        :param local_port: port of the running server you want to expose (ipport)
        :param remote_url: destination domain name (str)
        :param remote_port: remote tcprouter client port (usually 180000) (ippprt)
        :param secret: client secret (str) should match the secret on the servers's service
        :return: tcprouter client
        """
        client = j.clients.tcp_router.get(
            name,
            local_ip=local_ip,
            local_port=local_port,
            remote_url=remote_url,
            remote_port=remote_port,
            secret=secret,
        )
        client.connect()
        return client

    def test(self):
        """
        kosmos 'j.tools.tf_gateway.test()'

        :return:
        """
        self.domain_register_a("ns", "3bot.me", "134.209.90.92")
        self.domain_register_a("a", "3bot.me", "134.209.90.92")

        # to test
        # dig @ns1.name.com a.test.3bot.me

    def test_tcprouter_client(self):
        j.builders.network.tcprouter.start()

        j.sal.hostsfile.hostnames_set("127.0.0.1", ["myserver.local"])
        self.tcpservice_register(domain="myserver.local", client_secret="test_secret")

        # start a dummy python3 server
        python_server = j.servers.startupcmd.get("test_pythonserver", cmd_start="python3 -m http.server")
        python_server.start()

        client = self.create_tcprouter_service_client(
            "test_client",
            local_ip="127.0.0.1",
            local_port=80,
            remote_url="myserver.local",
            remote_port=18000,
            secret="test_secret",
        )

        time.sleep(2)
        assert requests.get("http://myserver.local").status_code == 200

        # tear down
        client.stop()
        client.delete()
        python_server.stop()
        j.builders.network.tcprouter.stop()

        j.core.db.delete("/tcprouter/service/myserver.local")

        print("TEST OK")
