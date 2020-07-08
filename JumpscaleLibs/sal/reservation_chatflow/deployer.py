from Jumpscale import j
from Jumpscale.servers.gedis.GedisChatBot import StopChatFlow
import netaddr


class ChatflowDeployer(j.baseclasses.object):
    __jslocation__ = "j.sal.chatflow_deployer"

    def _init(self, **kwargs):
        j.data.bcdb.get("tfgrid_solutions")
        self._explorer = j.clients.explorer.default

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

    def deploy_network(self, name, reservation, access_node, ip_range, ip_version, pool_id):
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
            ids.append(j.sal.zosv2.workloads.deploy(workload))
            parent_id = ids[-1]
        network_config["ids"] = ids
        network_config["rid"] = ids[0]
        return network_config

    def wait_workload(self, workload_id, bot):
        while True:
            workload = j.sal.zosv2.workloads.get(workload_id)
            remaning_time = j.data.time.secondsToHRDelta(workload.info.expiration_provisioning - j.data.time.epoch)
            deploying_message = f"""
            # Deploying...\n
            Deployment will be cancelled if it is not successful in {remaning_time}
            """
            bot.md_show_update(j.core.text.strip(deploying_message), md=True)
            if workload.info.result:
                return workload.info.result.state == "ok"
            if workload.info.expiration_provisioning < j.data.time.epoch:
                raise StopChatFlow(f"Workload {workload_id} failed to deploy in time")
