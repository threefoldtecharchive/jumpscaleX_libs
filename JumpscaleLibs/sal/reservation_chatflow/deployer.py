from Jumpscale import j
from Jumpscale.servers.gedis.GedisChatBot import StopChatFlow
import netaddr
from collections import defaultdict
import base64


class NetworkView:
    def __init__(self, name, workloads=None):
        self.name = name
        if not workloads:
            workloads = j.sal.zosv2.workloads.list(j.me.tid)
        self.workloads = workloads
        self.used_ips = []
        self.network_workloads = []
        self._fill_used_ips(self.workloads)
        self._init_network_workloads(self.workloads)
        self.pool_id = self.network_workloads[0].info.pool_id
        self.iprange = self.network_workloads[0].network_iprange

    def _fill_used_ips(self, workloads):
        for workload in workloads:
            if workload.info.next_action != "DEPLOY":
                continue
            if workload.info.workload_type == "KUBERNETES":
                self.used_ips.append(workload.ipaddress)
            elif workload.info.workload_type == "CONTAINER":
                for conn in workload.network_connection:
                    if conn.network_id == self.name:
                        self._fill_used_ips(conn.ipaddress)

    def _init_network_workloads(self, workloads):
        for workload in workloads:
            if workload.info.workload_type == "NETWORK_RESOURCE" and workload.name == self.name:
                self.network_workloads.append(workload)

    def add_node(self, node):
        used_ip_ranges = set()
        for workload in self.network_workloads:
            if workload.info.node_id == node.node_id:
                return
            used_ip_ranges.add(workload.iprange)
            for peer in workload.peers:
                used_ip_ranges.add(peer.iprange)
        else:
            network_range = netaddr.IPNetwork(self.iprange)
            for idx, subnet in enumerate(network_range.subnet(24)):
                if str(subnet) not in used_ip_ranges:
                    break
            else:
                self._bot.stop("Failed to find free network")
            reservation = j.sal.zosv2.reservation_create()
            network = j.sal.zosv2.network.create(reservation, self.iprange, self.name)
            j.sal.zosv2.network.add_node(network, node.node_id, str(subnet), self.pool_id)
            return network

    def get_node_range(self, node):
        for workload in self.network_workloads:
            if workload.info.node_id == node.node_id:
                return workload.iprange
        self._bot.stop(f"Node {node.node_id} is not part of network")

    @classmethod
    def copy(cls):
        return cls(cls.name)

    def get_node_free_ips(self, node, message):
        ip_range = self.get_node_range(node)
        freeips = []
        hosts = netaddr.IPNetwork(ip_range).iter_hosts()
        next(hosts)  # skip ip used by node
        for host in hosts:
            ip = str(host)
            if ip not in self.used_ips:
                freeips.append(ip)
        return freeips

    def get_free_ip(self, node):
        ip_range = self.get_node_range(node)
        hosts = netaddr.IPNetwork(ip_range).iter_hosts()
        next(hosts)  # skip ip used by node
        for host in hosts:
            ip = str(host)
            if ip not in self.used_ips:
                return ip
        return None


class ChatflowDeployer(j.baseclasses.object):
    __jslocation__ = "j.sal.chatflow_deployer"

    def _init(self, **kwargs):
        j.data.bcdb.get("tfgrid_solutions")
        self._explorer = j.clients.explorer.default
        self.workloads = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )  # Next Action: workload_type: pool_id: [workloads]

    def load_user_workloads(self):
        all_workloads = j.sal.zosv2.workloads.list(j.me.tid)
        keys = list(self.workloads.keys())
        for key in keys:
            self.workloads.pop(key)
        for workload in all_workloads:
            self.workloads[str(workload.info.next_action)][str(workload.info.workload_type)][
                workload.info.pool_id
            ].append(workload)

    def validate_user(self, user_info):
        if not j.core.myenv.config.get("THREEBOT_CONNECT", False):
            error_msg = """
            This chatflow is not supported when Threebot is in dev mode.
            To enable Threebot connect : `j.me.encryptor.tools.threebotconnect_enable()`
            """
            raise j.exceptions.Runtime(error_msg)
        if not user_info["email"]:
            raise j.exceptions.Value("Email shouldn't be empty")
        if not user_info["username"]:
            raise j.exceptions.Value("Name of logged in user shouldn't be empty")
        return self._explorer.users.get(name=user_info["username"], email=user_info["email"])

    def create_pool(self, bot):
        form = bot.new_form()
        cu = form.int_ask("Please specify the required CU")
        su = form.int_ask("Please specify the required SU")
        currencies = form.single_choice("Please choose the currency", ["TFT", "FreeTFT", "TFTA"])
        form.ask()
        cu = cu.value
        su = su.value
        currencies = currencies.value
        all_farms = self._explorer.farms.list()
        available_farms = {}
        for farm in all_farms:
            res = self.check_farm_capacity(farm.name, currencies, cru=cu, sru=su)
            available = res[0]
            resources = res[1:]
            if available:
                available_farms[farm.name] = resources
        farm_messages = {}
        for farm in available_farms:
            resources = available_farms[farm]
            farm_messages[
                f"{farm} cru: {resources[0]} sru: {resources[1]} hru: {resources[2]} mru {resources[3]}"
            ] = farm
        selected_farm = bot.single_choice("Please choose a farm", list(farm_messages.keys()))
        farm = farm_messages[selected_farm]
        try:
            pool_info = j.sal.zosv2.pools.create(cu, su, farm, currencies)
        except Exception as e:
            raise StopChatFlow(f"failed to reserve pool.\n{str(e)}")
        self.payment_show(pool_info, bot)
        return pool_info

    def extend_pool(self, bot, pool_id):
        form = bot.new_form()
        cu = form.int_ask("Please specify the required CU")
        su = form.int_ask("Please specify the required SU")
        currencies = form.single_choice("Please choose the currency", ["TFT", "FreeTFT", "TFTA"])
        form.ask()
        cu = cu.value
        su = su.value
        currencies = currencies.value
        try:
            pool_info = j.sal.zosv2.pools.extend(pool_id, cu, su, currencies=currencies)
        except Exception as e:
            raise StopChatFlow(f"failed to extend pool.\n{str(e)}")
        self.payment_show(pool_info, bot)
        return pool_info

    def check_farm_capacity(self, farm_name, currencies=[], sru=None, cru=None, mru=None, hru=None):
        farm_nodes = j.sal.zosv2.nodes_finder.nodes_search(farm_name=farm_name)
        available_cru = 0
        available_sru = 0
        available_mru = 0
        available_hru = 0
        for node in farm_nodes:
            if "FreeTFT" in currencies and not node.free_to_use:
                continue
            available_cru += node.total_resources.cru - node.used_resources.cru
            available_sru += node.total_resources.sru - node.used_resources.sru
            available_mru += node.total_resources.mru - node.used_resources.mru
            available_hru += node.total_resources.hru - node.used_resources.hru
        if sru and available_sru < sru:
            return False, available_cru, available_sru, available_mru, available_hru
        if cru and available_cru < cru:
            return False, available_cru, available_sru, available_mru, available_hru
        if mru and available_mru < mru:
            return False, available_cru, available_sru, available_mru, available_hru
        if hru and available_hru < hru:
            return False, available_cru, available_sru, available_mru, available_hru
        return True, available_cru, available_sru, available_mru, available_hru

    def list_pools(self, cu=None, su=None):
        all_pools = j.sal.zosv2.pools.list()
        available_pools = {}
        for pool in all_pools:
            res = self.check_pool_capacity(pool, cu, su)
            available = res[0]
            if available:
                resources = res[1:]
                available_pools[pool.pool_id] = resources
        return available_pools

    def select_pool(self, bot, cu=None, su=None, currency=None):
        available_pools = self.list_pools(cu, su)
        if not available_pools:
            raise StopChatFlow("no available pools")
        pool_messages = {}
        for pool in available_pools:
            pool_messages[f"Pool: {pool} cu: {available_pools[pool][0]} su: {available_pools[pool][1]}"] = pool
        pool = bot.single_choice("Please select a pool", list(pool_messages.keys()))
        return pool_messages[pool]

    def get_pool_farm_id(self, pool_id):
        pool = j.sal.zosv2.pools.get(pool_id)
        node_id = pool.node_ids[0]
        node = j.sal.zosv2._explorer.nodes.get(node_id)
        farm_id = node.farm_id
        return farm_id

    def check_pool_capacity(self, pool, cu=None, su=None):
        """
        pool: pool schema object
        """
        available_su = pool.sus - pool.active_su
        available_cu = pool.cus - pool.active_cu
        if cu and available_cu < cu:
            return False, available_cu, available_su
        if su and available_su < su:
            return False, available_cu, available_su
        return True, available_cu, available_su

    def payment_show(self, pool, bot):
        escrow_info = pool.escrow_information
        resv_id = pool.reservation_id
        escrow_address = escrow_info.address
        escrow_asset = escrow_info.asset
        total_amount = escrow_info.amount
        wallets = j.sal.reservation_chatflow.wallets_list()
        wallet_names = []
        for w in wallets.keys():
            wallet_names.append(w)
        wallet_names.append("3bot app")
        message = f"""
        Billing details:
        <h4> Wallet address: </h4>  {escrow_address} \n
        <h4> Currency: </h4>  {escrow_asset} \n
        <h4> Choose a wallet name to use for payment or proceed with payment through 3bot app </h4>
        """
        result = bot.single_choice(message, wallet_names, html=True)
        if result == "3bot app":
            qr_code = f"{escrow_asset.split(':')[0]}:{escrow_address}?amount={total_amount}&message={resv_id}&sender=me"
            msg_text = f"""
            <h3> Please make your payment </h3>
            Scan the QR code with your application (do not change the message) or enter the information below manually and proceed with the payment. Make sure to add the reservationid as memo_text.

            <h4> Wallet address: </h4>  {escrow_address} \n
            <h4> Currency: </h4>  {escrow_asset} \n
            <h4> Reservation id: </h4>  {resv_id} \n
            <h4> Total Amount: </h4> {total_amount} \n
            """
            bot.qrcode_show(data=qr_code, msg=msg_text, scale=4, update=True, html=True)
        else:
            wallet = wallets[result]
            pass
            # TODO: implement wallet payments

    def ask_expiration(self, bot):
        expiration = bot.datetime_picker(
            "Please enter network expiration time.",
            required=True,
            min_time=[3600, "Date/time should be at least 1 hour from now"],
            default=j.data.time.epoch + 3900,
        )
        return expiration

    def ask_currency(self, bot):
        currency = bot.single_choice(
            "Please choose a currency that will be used for the payment",
            ["FreeTFT", "TFTA", "TFT"],
            default="TFT",
            required=True,
        )
        return currency

    def ask_name(self, bot):
        name = bot.string_ask("Please enter a name for you workload", required=True, field="name")
        return name

    def encrypt_metadata(self, metadata):
        if isinstance(metadata, dict):
            metadata = j.data.serializers.json.dumps(metadata)
        encrypted_metadata = base64.b85encode(j.me.encryptor.encrypt(metadata.encode())).decode()
        return encrypted_metadata

    def decrypt_metadata(self, encrypted_metadata):
        try:
            return j.me.encryptor.decrypt(base64.b85decode(encrypted_metadata.encode())).decode()
        except:
            return ""

    def deploy_network(self, name, reservation, access_node, ip_range, ip_version, pool_id, **metadata):
        network = j.sal.zosv2.network.create(reservation, ip_range, name)
        node_subnets = netaddr.IPNetwork(ip_range).subnet(24)
        network_config = dict()
        use_ipv4 = ip_version == "IPv4"

        j.sal.zosv2.network.add_node(network, access_node.node_id, str(next(node_subnets)), pool_id)
        wg_quick = j.sal.zosv2.network.add_access(network, access_node.node_id, str(next(node_subnets)), ipv4=use_ipv4)

        network_config["wg"] = wg_quick
        j.sal.fs.writeFile(f"/sandbox/cfg/wireguard/{name}.conf", f"{wg_quick}")

        ids = []
        parent_id = None
        encrypted_metadata = ""
        if metadata:
            encrypted_metadata = self.encrypt_metadata(metadata)
        for workload in network.network_resources:
            workload.info.description = j.data.serializers.json.dumps({"parent_id": parent_id})
            workload.metadata = encrypted_metadata
            ids.append(j.sal.zosv2.workloads.deploy(workload))
            parent_id = ids[-1]
        network_config["ids"] = ids
        network_config["rid"] = ids[0]
        return network_config

    def add_network_node(self, name, node, network_view=None, **metadata):
        if not network_view:
            network_view = NetworkView(name)
        network = network_view.add_node(node)
        if not network:
            return
        parent_id = network_view.network_workloads[-1].id
        ids = []
        encrypted_metadata = ""
        if metadata:
            encrypted_metadata = self.encrypt_metadata(metadata)
        for workload in network.network_resources:
            workload.info.description = j.data.serializers.json.dumps({"parent_id": parent_id})
            workload.metadata = encrypted_metadata
            ids.append(j.sal.zosv2.workloads.deploy(workload))
            parent_id = ids[-1]
        return {"ids": ids, "rid": ids[0]}

    def wait_workload(self, workload_id, bot):
        while True:
            workload = j.sal.zosv2.workloads.get(workload_id)
            remaning_time = j.data.time.secondsToHRDelta(workload.info.expiration_provisioning - j.data.time.epoch)
            deploying_message = f"""
            # Deploying...\n
            Deployment will be cancelled if it is not successful in {remaning_time}
            """
            bot.md_show_update(j.core.text.strip(deploying_message), md=True)
            if workload.info.result.workload_id:
                return workload.info.result.state == "ok"
            if workload.info.expiration_provisioning < j.data.time.epoch:
                raise StopChatFlow(f"Workload {workload_id} failed to deploy in time")

    def list_networks(self, next_action="DEPLOY", capacity_pool_id=None):
        self.load_user_workloads()
        networks = {}  # name: last child network resource
        for pool_id in self.workloads[next_action]["NETWORK_RESOURCE"]:
            if capacity_pool_id and capacity_pool_id != pool_id:
                continue
            for workload in self.workloads[next_action]["NETWORK_RESOURCE"][pool_id]:
                networks[workload.name] = workload
        all_workloads = []
        for pools_workloads in self.workloads[next_action].values():
            for pool_id, workload_list in pools_workloads.items():
                if capacity_pool_id and capacity_pool_id != pool_id:
                    continue
                all_workloads += workload_list
        network_views = {}
        for network_name in networks:
            network_views[network_name] = NetworkView(network_name, all_workloads)
        return network_views

    def select_network(self, bot, pool_id):
        network_views = self.list_networks(capacity_pool_id=pool_id)
        if not network_views:
            raise StopChatFlow(f"There are no available networks in this pool: {pool_id}")
        network_name = bot.single_choice("Please select a network", list(network_views.keys()))
        return network_views[network_name]

    def deploy_volume(self, pool_id, node_id, size, volume_type="SSD", **metadata):
        reservation = j.sal.zosv2.reservation_create()
        volume = j.sal.zosv2.volume.create(reservation, node_id, pool_id, size, volume_type)
        if metadata:
            volume.info.metadata = self.encrypt_metadata(metadata)
        return j.sal.zosv2.workloads.deploy(volume)

    def deploy_container(
        self,
        pool_id,
        node_id,
        network_name,
        ip_address,
        flist,
        env=None,
        cpu=1,
        memory=1024,
        disk_size=256,
        disk_type="SSD",
        entrypoint="",
        interactive=False,
        secret_env=None,
        volumes=None,
        log_config=None,
        **metadata,
    ):
        """
        volumes: dict {"mountpoint (/)": volume_id}
        log_Config: dict. keys ("channel_type", "channel_host", "channel_port", "channel_name")
        """
        resevation = j.sal.zosv2.reservation_create()
        encrypted_secret_env = {}
        if secret_env:
            for key, val in secret_env.items():
                encrypted_secret_env[key] = j.sal.zosv2.container.encrypt_secret(node_id, val)
        container = j.sal.zosv2.container.create(
            resevation,
            node_id,
            network_name,
            ip_address,
            flist,
            pool_id,
            env,
            cpu,
            memory,
            disk_size,
            disk_type,
            entrypoint,
            interactive,
            secret_env,
        )
        if volumes:
            for mount_point, vol_id in volumes.items():
                j.sal.zosv2.volume.attach_existing(container, vol_id, mount_point)
        if metadata:
            container.info.metadata = self.encrypt_metadata(metadata)
        if log_config:
            j.sal.zosv2.container.add_logs(container, **log_config)
        return j.sal.zosv2.workloads.deploy(container)

    def ask_container_resources(self, bot, cpu=True, memory=True, disk_size=True, disk_type=False):
        form = bot.new_form()
        if cpu:
            cpu_answer = form.int_ask("Please specify how many cpus", default=1)
        if memory:
            memory_answer = form.int_ask("Please specify how much memory", default=1024)
        if disk_size:
            disk_size_answer = form.int_ask("Please specify the size of root filesystem", default=256)
        if disk_type:
            disk_type_answer = form.single_choice("Please choose the root filesystem disktype", ["SSD", "HDD"])
        form.ask()
        resources = {}
        if cpu:
            resources["cpu"] = cpu_answer.value
        if memory:
            resources["memory"] = memory_answer.value
        if disk_size:
            resources["disk_size"] = disk_size_answer.value
        if disk_type:
            resources["disk_type"] = disk_type_answer.value
        return resources

    def ask_container_logs(self, bot, solution_name=None):
        logs_config = {}
        form = bot.new_form()
        channel_type = form.string_ask("Please add the channel type", default="redis", required=True)
        channel_host = form.string_ask("Please add the IP address where the logs will be output to", required=True)
        channel_port = form.int_ask("Please add the port available where the logs will be output to", required=True)
        channel_name = form.string_ask(
            "Please add the channel name to be used. The channels will be in the form NAME-stdout and NAME-stderr",
            default=solution_name,
            required=True,
        )
        form.ask()
        logs_config["channel_type"] = channel_type.value
        logs_config["channel_host"] = channel_host.value
        logs_config["channel_port"] = channel_port.value
        logs_config["channel_name"] = channel_name.value
        return logs_config

    def schedule_container(self, pool_id, cru=None, sru=None, mru=None, hru=None, ip_version=None):
        pool = j.sal.zosv2.pools.get(pool_id)
        res = self.check_pool_capacity(pool, cru, sru)
        if not res[0]:
            raise StopChatFlow(
                f"Not enough resources in pool {pool_id}\n available cu: {res[1]} available su: {res[2]}"
            )
        farm_id = self.get_pool_farm_id(pool_id)
        farm_name = j.sal.zosv2._explorer.farms.get(farm_id).name
        query = {"cru": cru, "sru": sru, "mru": mru, "hru": hru, "ip_version": ip_version}
        return j.sal.reservation_chatflow.nodes_get(1, farm_names=[farm_name], **query)[0]

    def ask_container_placement(
        self, bot, pool_id, cru=None, sru=None, mru=None, hru=None, ip_version=None, free_to_use=False
    ):
        manual_choice = bot.single_choice(
            "Do you want to manually select a node deployment or automatically?", ["YES", "NO"]
        )
        if manual_choice == "NO":
            return None
        farm_id = self.get_pool_farm_id(pool_id)
        nodes = j.sal.zosv2.nodes_finder.nodes_by_capacity(farm_id=farm_id, cru=cru, sru=sru, mru=mru, hru=hru)
        nodes = list(nodes)
        nodes = j.sal.reservation_chatflow.nodes_filter(nodes, free_to_use, ip_version)
        if not nodes:
            raise StopChatFlow("Failed to find resources for this reservation")
        node_messages = {node.node_id: node for node in nodes}
        node_id = bot.drop_down_choice("Please choose the node you want to deploy on", list(node_messages.keys()))
        return node_messages[node_id]
