from Jumpscale import j
from Jumpscale.servers.gedis.GedisChatBot import StopChatFlow
import netaddr
from collections import defaultdict
import base64
from decimal import Decimal
import math


class NetworkView:
    def __init__(self, name, pool_id, workloads=None):
        self.name = name
        self.pool_id = pool_id
        if not workloads:
            workloads = j.sal.zosv2.workloads.list(j.me.tid)
        self.workloads = workloads
        self.used_ips = []
        self.network_workloads = []
        self._fill_used_ips(self.workloads)
        self._init_network_workloads(self.workloads)
        self.iprange = self.network_workloads[0].network_iprange

    def _fill_used_ips(self, workloads):
        for workload in workloads:
            if workload.info.pool_id != self.pool_id:
                continue
            if workload.info.next_action != "DEPLOY":
                continue
            if workload.info.workload_type == "KUBERNETES":
                self.used_ips.append(workload.ipaddress)
            elif workload.info.workload_type == "CONTAINER":
                for conn in workload.network_connection:
                    if conn.network_id == self.name:
                        self.used_ips.append(conn.ipaddress)

    def _init_network_workloads(self, workloads):
        for workload in workloads:
            if workload.info.pool_id != self.pool_id:
                continue
            if workload.info.next_action != "DEPLOY":
                continue
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
                raise StopChatFlow("Failed to find free network")
            reservation = j.sal.zosv2.reservation_create()
            network = j.sal.zosv2.network.create(reservation, self.iprange, self.name)
            # network.network_resources.append(self.network_workloads[-1])
            j.sal.zosv2.network.add_node(network, node.node_id, str(subnet), self.pool_id)
            j.sal.zosv2.network.add_access(network, node.node_id, str(subnet))
            return network

    def get_node_range(self, node):
        for workload in self.network_workloads:
            if workload.info.pool_id != self.pool_id:
                continue
            if workload.info.node_id == node.node_id:
                return workload.iprange
        raise StopChatFlow(f"Node {node.node_id} is not part of network")

    def copy(self):
        return NetworkView(self.name, self.pool_id)

    def get_node_free_ips(self, node):
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
            if workload.info.metadata:
                workload.info.metadata = self.decrypt_metadata(workload.info.metadata)
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
            res = self.check_farm_capacity(farm.name, currencies, cru=None, sru=None)
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
        self.show_payment(pool_info, bot)
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
        self.show_payment(pool_info, bot)
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

    def select_pool(self, bot, cu=None, su=None):
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
        if pool.empty_at < 0:
            return False, 0, 0
        if cu and available_cu < cu:
            return False, available_cu, available_su
        if su and available_su < su:
            return False, available_cu, available_su
        return True, available_cu, available_su

    def show_payment(self, pool, bot):
        escrow_info = pool.escrow_information
        resv_id = pool.reservation_id
        escrow_address = escrow_info.address
        escrow_asset = escrow_info.asset
        total_amount = escrow_info.amount
        total_amount_dec = Decimal(total_amount) / Decimal(1e7)
        total_amount = "{0:f}".format(total_amount_dec)

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
            qr_code = (
                f"{escrow_asset.split(':')[0]}:{escrow_address}?amount={total_amount}&message=p-{resv_id}&sender=me"
            )
            msg_text = f"""
            <h3> Please make your payment </h3>
            Scan the QR code with your application (do not change the message) or enter the information below manually and proceed with the payment. Make sure to add the reservationid as memo_text.

            <h4> Wallet address: </h4>  {escrow_address} \n
            <h4> Currency: </h4>  {escrow_asset} \n
            <h4> Reservation id: </h4>  p-{resv_id} \n
            <h4> Total Amount: </h4> {total_amount} \n
            """
            bot.qrcode_show(data=qr_code, msg=msg_text, scale=4, update=True, html=True)
        else:
            wallet = wallets[result]
            wallet.transfer(
                destination_address=escrow_address,
                amount=total_amount,
                asset=escrow_asset.split(":")[0],
                memo_text=f"p-{resv_id}",
            )

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
            return "{}"

    def deploy_network(self, name, access_node, ip_range, ip_version, pool_id, **metadata):
        reservation = j.sal.zosv2.reservation_create()
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
        for workload in network.network_resources:
            workload.info.description = j.data.serializers.json.dumps({"parent_id": parent_id})
            metadata["parent_network"] = parent_id
            workload.metadata = self.encrypt_metadata(metadata)
            ids.append(j.sal.zosv2.workloads.deploy(workload))
            parent_id = ids[-1]
        network_config["ids"] = ids
        network_config["rid"] = ids[0]
        return network_config

    def add_network_node(self, name, node, pool_id, network_view=None, **metadata):
        if not network_view:
            network_view = NetworkView(name, pool_id)
        network = network_view.add_node(node)
        if not network:
            return
        parent_id = network_view.network_workloads[-1].id
        ids = []
        for workload in network.network_resources:
            workload.info.description = j.data.serializers.json.dumps({"parent_id": parent_id})
            metadata["parent_network"] = parent_id
            workload.metadata = self.encrypt_metadata(metadata)
            ids.append(j.sal.zosv2.workloads.deploy(workload))
            parent_id = ids[-1]
        return {"ids": ids, "rid": ids[0]}

    def wait_workload(self, workload_id, bot=None):
        expiration_provisioning = j.data.time.getEpochDeltaTime("15m")
        while True:
            workload = j.sal.zosv2.workloads.get(workload_id)
            remaning_time = j.data.time.secondsToHRDelta(expiration_provisioning - j.data.time.epoch)
            deploying_message = f"""
            # Deploying...\n
            Deployment will be cancelled if it is not successful in {remaning_time}
            """
            if bot:
                bot.md_show_update(j.core.text.strip(deploying_message), md=True)
            if workload.info.result.workload_id:
                return workload.info.result.state == "ok"
            if expiration_provisioning < j.data.time.epoch:
                raise StopChatFlow(f"Workload {workload_id} failed to deploy in time")

    def list_networks(self, next_action="DEPLOY", capacity_pool_id=None, sync=True):
        if sync:
            self.load_user_workloads()
        networks = {}  # name: last child network resource
        for pool_id in self.workloads[next_action]["NETWORK_RESOURCE"]:
            if capacity_pool_id and capacity_pool_id != pool_id:
                continue
            for workload in self.workloads[next_action]["NETWORK_RESOURCE"][pool_id]:
                networks[f"{capacity_pool_id}-{workload.name}"] = workload
        all_workloads = []
        for pools_workloads in self.workloads[next_action].values():
            for pool_id, workload_list in pools_workloads.items():
                if capacity_pool_id and capacity_pool_id != pool_id:
                    continue
                all_workloads += workload_list
        network_views = {}
        for network_name in networks:
            name = network_name.split("-")[1]
            network_views[network_name] = NetworkView(name, networks[network_name].info.pool_id, all_workloads)
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
        public_ipv6=False,
        **metadata,
    ):
        """
        volumes: dict {"mountpoint (/)": volume_id}
        log_Config: dict. keys ("channel_type", "channel_host", "channel_port", "channel_name")
        """
        reservation = j.sal.zosv2.reservation_create()
        encrypted_secret_env = {}
        if secret_env:
            for key, val in secret_env.items():
                encrypted_secret_env[key] = j.sal.zosv2.container.encrypt_secret(node_id, val)
        container = j.sal.zosv2.container.create(
            reservation,
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
            public_ipv6=public_ipv6,
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
        farm_id = self.get_pool_farm_id(pool_id)
        farm_name = j.sal.zosv2._explorer.farms.get(farm_id).name
        query = {"cru": cru, "sru": sru, "mru": mru, "hru": hru, "ip_version": ip_version}
        return j.sal.reservation_chatflow.nodes_get(1, farm_names=[farm_name], **query)[0]

    def ask_container_placement(
        self,
        bot,
        pool_id,
        cru=None,
        sru=None,
        mru=None,
        hru=None,
        ip_version=None,
        free_to_use=False,
        workload_name=None,
    ):
        if not workload_name:
            workload_name = "your workload"
        manual_choice = bot.single_choice(
            f"Do you want to manually select a node for deployment or automatically for {workload_name}?", ["YES", "NO"]
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
        node_id = bot.drop_down_choice(
            f"Please choose the node you want to deploy {workload_name} on", list(node_messages.keys())
        )
        return node_messages[node_id]

    def delegate_domain(self, pool_id, gateway_id, domain_name, **metadata):
        reservation = j.sal.zosv2.reservation_create()
        domain_delegate = j.sal.zosv2.gateway.delegate_domain(reservation, gateway_id, domain_name, pool_id)
        if metadata:
            domain_delegate.info.metadata = self.encrypt_metadata(metadata)
        return j.sal.zosv2.workloads.deploy(domain_delegate)

    def deploy_kubernetes_master(
        self, pool_id, node_id, network_name, cluster_secret, ssh_keys, ip_address, size=1, **metadata
    ):
        reservation = j.sal.zosv2.reservation_create()
        master = j.sal.zosv2.kubernetes.add_master(
            reservation, node_id, network_name, cluster_secret, ip_address, size, ssh_keys, pool_id
        )
        master.info.description = j.data.serializers.json.dumps({"role": "master"})
        if metadata:
            master.info.metadata = self.encrypt_metadata(metadata)
        return j.sal.zosv2.workloads.deploy(master)

    def deploy_kubernetes_worker(
        self, pool_id, node_id, network_name, cluster_secret, ssh_keys, ip_address, master_ip, size=1, **metadata
    ):
        reservation = j.sal.zosv2.reservation_create()
        worker = j.sal.zosv2.kubernetes.add_worker(
            reservation, node_id, network_name, cluster_secret, ip_address, size, master_ip, ssh_keys, pool_id
        )
        worker.info.description = j.data.serializers.json.dumps({"role": "worker"})
        if metadata:
            worker.info.metadata = self.encrypt_metadata(metadata)
        return j.sal.zosv2.workloads.deploy(worker)

    def deploy_kubernetes_cluster(
        self, pool_id, node_ids, network_name, cluster_secret, ssh_keys, size=1, ip_addresses=None, **metadata,
    ):
        """
        deplou k8s cluster with the same number of nodes as specifed in node_ids

        Args:
            node_ids: list() of node ids to deploy on. first node_id is used for master reservation
            ip_addresses: if specified it will be mapped 1-1 with node_ids for workloads. if not specified it will choose any free_ip from the node

        Return:
            list: [{"node_id": "ip_address"}, ...] first dict is master's result
        """
        result = []  # [{"node_id": id,  "ip_address": ip, "reservation_id": 16}] first dict is master's result
        if ip_addresses and len(ip_addresses) != len(node_ids):
            raise StopChatFlow("length of ips != node_ids")

        if not ip_addresses:
            # get free_ips for the nodes
            ip_addresses = []
            for node_id in node_ids:
                node = j.sal.zosv2._explorer.nodes.get(node_id)
                res = self.add_network_node(network_name, node, pool_id)
                if res:
                    for wid in res["ids"]:
                        success = self.wait_workload(wid)
                        if not success:
                            raise StopChatFlow(f"Failed to add node {node.node_id} to network {wid}")
                network_view = NetworkView(network_name, pool_id)
                address = network_view.get_free_ip(node)
                if not address:
                    raise StopChatFlow(f"No free IPs for network {network_name} on the specifed node {node_id}")
                ip_addresses.append(address)

        # deploy_master
        master_ip = ip_addresses[0]
        master_resv_id = self.deploy_kubernetes_master(
            pool_id, node_ids[0], network_name, cluster_secret, ssh_keys, master_ip, size, **metadata
        )
        result.append({"node_id": node_ids[0], "ip_address": master_ip, "reservation_id": master_resv_id})
        for i in range(1, len(node_ids)):
            node_id = node_ids[i]
            ip_address = ip_addresses[i]
            resv_id = self.deploy_kubernetes_worker(
                pool_id, node_id, network_name, cluster_secret, ssh_keys, ip_address, master_ip, size, **metadata
            )
            result.append({"node_id": node_id, "ip_address": ip_address, "reservation_id": resv_id})
        return result

    def list_gateways(self, pool_id):
        """
        return dict of gateways where keys are descriptive string of each gateway
        """
        farm_id = self.get_pool_farm_id(pool_id)
        gateways = j.sal.zosv2._explorer.gateway.list(farm_id=farm_id)
        if not gateways:
            raise StopChatFlow(f"no available gateways in pool {pool_id} farm: {farm_id}")
        result = {}
        for g in gateways:
            if not g.dns_nameserver:
                continue
            result[f"{g.dns_nameserver[0]} {g.location.continent} {g.location.country} {g.node_id}"] = g
        return result

    def select_gateway(self, bot, pool_id):
        gateways = self.list_gateways(pool_id)
        selected = bot.single_choice("Please select a gateway", list(gateways.keys()))
        return gateways[selected]

    def create_ipv6_gateway(self, gateway_id, pool_id, public_key, **metadata):
        reservation = j.sal.zosv2.reservation_create()
        workload = j.sal.zosv2.gateway.gateway_4to6(reservation, gateway_id, public_key, pool_id)
        if metadata:
            workload.info.metadata = self.encrypt_metadata(metadata)
        return j.sal.zosv2.workloads.deploy(workload)

    def deploy_zdb(self, pool_id, node_id, size, mode, password, disk_type="SSD", public=False, **metadata):
        reservation = j.sal.zosv2.reservation_create()
        workload = j.sal.zosv2.zdb.create(reservation, node_id, size, mode, password, pool_id, disk_type, public)
        if metadata:
            workload.info.metadata = self.encrypt_metadata(metadata)
        return j.sal.zosv2.workloads.deploy(workload)

    def create_subdomain(self, pool_id, gateway_id, subdomain, addresses=None, **metadata):
        """
        creates an A record pointing to the specified addresses
        if no addresses are specified, the record will point the gateway IP address (used for exposing solutions)
        """
        if not addresses:
            gateway = j.sal.zosv2._explorer.gateway.get(gateway_id)
            addresses = [j.sal.nettools.getHostByName(ns) for ns in gateway.dns_nameserver]
        reservation = j.sal.zosv2.reservation_create()
        workload = j.sal.zosv2.gateway.sub_domain(reservation, gateway_id, subdomain, addresses, pool_id)
        if metadata:
            workload.info.metadata = self.encrypt_metadata(metadata)
        return j.sal.zosv2.workloads.deploy(workload)

    def create_proxy(self, pool_id, gateway_id, domain_name, trc_secret, **metadata):
        """
        creates a reverse tunnel on the gateway node
        """
        reservation = j.sal.zosv2.reservation_create()
        workload = j.sal.zosv2.gateway.tcp_proxy_reverse(reservation, gateway_id, domain_name, trc_secret, pool_id)
        if metadata:
            workload.info.metadata = self.encrypt_metadata(metadata)
        return j.sal.zosv2.workloads.deploy(workload)

    def expose_address(self, pool_id, gateway_id, network_name, local_ip, port, tls_port, trc_secret, **metadata):
        gateway = j.sal.zosv2._explorer.gateway.get(gateway_id)
        remote = f"{gateway.dns_nameserver[0]}:{gateway.tcp_router_port}"
        secret_env = {"TRC_SECRET": trc_secret}
        entry_point = f"/bin/trc -local {local_ip}:{port} -local-tls {local_ip}:{tls_port} -remote {remote}"
        node = self.schedule_container(pool_id=pool_id, cru=1, mru=1, sru=1)

        res = self.add_network_node(network_name, node, pool_id)
        if res:
            for wid in res["ids"]:
                success = self.wait_workload(wid)
                if not success:
                    raise StopChatFlow(f"Failed to add node {node.node_id} to network {wid}")
        network_view = NetworkView(network_name, pool_id)
        ip_address = network_view.get_free_ip(node)

        resv_id = self.deploy_container(
            pool_id=pool_id,
            node_id=node.node_id,
            network_name=network_name,
            ip_address=ip_address,
            flist="https://hub.grid.tf/tf-official-apps/tcprouter:latest.flist",
            disk_type="HDD",
            entrypoint=entry_point,
            secret_env=secret_env,
            **metadata,
        )
        return resv_id

    def deploy_minio_zdb(
        self, pool_id, password, node_ids=None, zdb_no=None, disk_type="SSD", disk_size=10, **metadata
    ):
        """
        deploy zdb workloads on the specified node_ids if specified or deploy workloads as specifdied by the zdb_no
        """
        result = []
        if not node_ids and zdb_no:
            query = {}
            if disk_type == "SSD":
                query["sru"] = math.ceil(disk_size / 1024)
            else:
                query["hru"] = math.ceil(disk_size / 1024)
            farm_id = self.get_pool_farm_id(pool_id)
            nodes = j.sal.reservation_chatflow.nodes_get(farm_id=farm_id, number_of_nodes=zdb_no, **query)
        for node in nodes:
            node_id = node.node_id
            resv_id = self.deploy_zdb(
                pool_id=pool_id,
                node_id=node_id,
                size=disk_size,
                mode="seq",
                password=password,
                disk_type=disk_type,
                **metadata,
            )
            result.append(resv_id)
        return result

    def deploy_minio_containers(
        self,
        pool_id,
        network_name,
        minio_nodes,
        minio_ip_addresses,
        zdb_configs,
        ak,
        sk,
        ssh_key,
        cpu,
        memory,
        data,
        parity,
        disk_type="SSD",
        disk_size=10,
        log_config=None,
        mode="Single",
        **metadata,
    ):
        secret_env = {}
        if mode == "Master/Slave":
            secret_env["TLOG"] = zdb_configs.pop(-1)
        shards = ",".join(zdb_configs)
        secret_env["SHARDS"] = shards
        secret_env["SECRET_KEY"] = sk
        env = {
            "DATA": data,
            "PARITY": parity,
            "ACCESS_KEY": ak,
            "SSH_KEY": ssh_key,
            "MINIO_PROMETHEUS_AUTH_TYPE": "public",
        }
        result = []
        master_volume_id = self.deploy_volume(pool_id, minio_nodes[0], disk_size, disk_type, **metadata)
        success = self.wait_workload(master_volume_id)
        if not success:
            raise StopChatFlow(
                f"Failed to create volume {master_volume_id} for minio container on node {minio_nodes[0]}"
            )
        master_cont_id = self.deploy_container(
            pool_id=pool_id,
            node_id=minio_nodes[0],
            network_name=network_name,
            ip_address=minio_ip_addresses[0],
            env=env,
            cpu=cpu,
            memory=memory,
            secret_env=secret_env,
            log_config=log_config,
            volumes={"/data", master_volume_id},
        )
        result.append(master_cont_id)
        if mode == "Master/Slave":
            secret_env["MASTER"] = secret_env.pop("TLOG")
            slave_volume_id = self.deploy_volume(pool_id, minio_nodes[1], disk_size, disk_type, **metadata)
            success = self.wait_workload(slave_volume_id)
            if not success:
                raise StopChatFlow(
                    f"Failed to create volume {slave_volume_id} for minio container on node {minio_nodes[1]}"
                )
            slave_cont_id = self.deploy_container(
                pool_id=pool_id,
                node_id=minio_nodes[1],
                network_name=network_name,
                ip_address=minio_ip_addresses[1],
                env=env,
                cpu=cpu,
                memory=memory,
                secret_env=secret_env,
                log_config=log_config,
                volumes={"/data", master_volume_id},
                flist="https://hub.grid.tf/tf-official-apps/minio:latest.flist",
            )
            result.append(slave_cont_id)
        return result

    def get_zdb_url(self, zdb_id, password):
        workload = j.sal.zosv2.workloads.get(zdb_id)
        if "IPs" in workload.result["data_json"]:
            ip = workload.result["data_json"]["IPs"][0]
        else:
            ip = workload.result["data_json"]["IP"]
        namespace = workload.result["data_json"]["Namespace"]
        port = workload.result["data_json"]["Port"]
        url = f"{namespace}:{password}@[{ip}]:{port}"
        return url

    def calculate_capacity_units(self, cru=0, mru=0, sru=0, hru=0):
        """
        return cu, su
        """
        cu = min(cru * 4, (mru - 1) / 4)
        su = hru / 1000 / 1.2 + sru / 100 / 1.2
        return cu, su

    def get_network_view(self, network_name, pool_id, workloads=None):
        return NetworkView(network_name, pool_id, workloads)
