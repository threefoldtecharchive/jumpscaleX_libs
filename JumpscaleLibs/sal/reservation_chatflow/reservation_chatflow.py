import netaddr
from Jumpscale import j
import random
import copy


class Chatflow(j.baseclasses.object):
    __jslocation__ = "j.sal.reservation_chatflow"

    def _init(self, **kwargs):
        j.data.bcdb.get("tfgrid_solutions")

    def get_all_ips(self, ip_range):
        """
        ip_range: (String)ip range of network
        return all available ips of this network
        """
        networks = netaddr.IPNetwork(ip_range)
        ips = []
        all_ips = list(networks.iter_hosts())
        for i, ip in enumerate(all_ips):
            if i == 0 or i == len(all_ips) - 1:
                continue
            ips.append(ip.format())
        return ips

    def nodes_get(
        self, number_of_nodes, ip_version, farm_id=None, farm_name=None, cru=None, sru=None, mru=None, hru=None
    ):
        # get nodes without public ips
        access_nodes_filter = []
        nodes = j.sal.zosv2.nodes_finder.nodes_by_capacity(
            farm_id=farm_id, farm_name=farm_name, cru=cru, sru=sru, mru=mru, hru=hru
        )  # Choose free farm

        access_nodes = j.sal.zosv2.nodes_finder.nodes_search(farm_id=71)
        if ip_version == "IPv4":
            for node in filter(j.sal.zosv2.nodes_finder.filter_public_ip4, access_nodes):
                access_nodes_filter.append(node)
        else:
            for node in filter(j.sal.zosv2.nodes_finder.filter_public_ip6, access_nodes):
                access_nodes_filter.append(node)

        # to avoid using the same node with different networks
        nodes = set(list(nodes)) - set(access_nodes_filter)
        nodes_selected = []
        nodes = list(nodes)
        for i in range(number_of_nodes):
            node = random.choice(nodes)
            while not j.sal.zosv2.nodes_finder.filter_is_up(node):
                node = random.choice(nodes)
            nodes_selected.append(node)
        return nodes_selected

    def network_configure(
        self, bot, reservation, nodes, customer_tid, ip_version, number_of_ipaddresses=0, expiration=None
    ):
        """
        bot: Gedis chatbot object from chatflow
        reservation: reservation object from schema
        node: list of node objects from explorer

        return reservation (Object) , config of network (dict)
        """
        reservation_copy = copy.copy(reservation)
        explorer = j.clients.explorer.default
        expiration = expiration or j.data.time.epoch + (60 * 60 * 24)
        networks_name = []
        network_user_choice = ""
        while (networks_name == [] and network_user_choice == "Existing network") or network_user_choice == "":
            network_choice = ["New network", "Existing network"]
            network_user_choice = bot.single_choice("Create a new network or use an existing one.", network_choice)
            if network_user_choice == "New network":
                ip_range = self.ip_range_get(bot)
                reservation, network_config = self.network_get(
                    bot, reservation, ip_range, nodes, customer_tid, ip_version, number_of_ipaddresses, expiration
                )
            else:
                networks = self.network_exists(customer_tid)
                for n in networks.keys():
                    networks_name.append(n)
                if networks_name == []:
                    res = "<h2> You don't have any network previously created </h2>"
                    res = j.tools.jinja2.template_render(text=res)
                    bot.md_show(res)
                    continue
                network = bot.single_choice("Choose a network that you have previously created", networks_name)
                reservation, network_config = self.add_node_to_network_exists(
                    bot, reservation, nodes, networks[network], expiration, customer_tid=customer_tid
                )
                ip_range = networks[network].iprange

        network_config["ip_range"] = ip_range
        network_config["user_choice"] = network_user_choice
        # Check if reservation failed
        result_check = False
        while not result_check:
            resv_id = network_config["rid"]
            reservation_results = explorer.reservations.get(resv_id).results
            port_error = False
            for result in reservation_results:
                if result.state == "ERROR" and "wireguard listen port already in use" in result.message:
                    port_error = True
                    break
            if port_error:
                # Cancel failed reservation
                j.sal.zosv2.reservation_cancel(resv_id)
                reservation = reservation_copy
                reservation_copy = copy.copy(reservation)
                if network_config["user_choice"] == "New network":
                    # Need to re do the reservation with another port
                    reservation, network_config = self.network_get(
                        bot,
                        reservation,
                        ip_range,
                        nodes,
                        customer_tid,
                        ip_version,
                        number_of_ipaddresses,
                        interactive=False,
                        noninteractive_args=network_config,
                    )
                else:
                    reservation, network_config = self.add_node_to_network_exists(
                        bot, reservation, nodes, networks[network], expiration, customer_tid=customer_tid
                    )

            else:
                result_check = len(reservation_results) == len(nodes)

        return reservation, network_config

    def ip_range_get(self, bot):
        """
        bot: Gedis chatbot object from chatflow
        return ip_range from user or generated one
        """
        ip_range_choose = ["Configure IP range myself", "Choose IP range for me"]
        iprange_user_choice = bot.single_choice(
            "To have access to the threebot, the network must be configured", ip_range_choose
        )
        if iprange_user_choice == "Configure IP range myself":
            ip_range = bot.string_ask("Please add private IP Range of the network")
        else:
            first_digit = random.choice([172, 10])
            if first_digit == 10:
                second_digit = random.randint(0, 255)
            else:
                second_digit = random.randint(16, 31)
            ip_range = str(first_digit) + "." + str(second_digit) + ".0.0/16"
        return ip_range

    def network_get(
        self,
        bot,
        reservation,
        ip_range,
        nodes,
        customer_tid,
        ip_version,
        number_of_ipaddresses=0,
        interactive=True,
        noninteractive_args=None,
        expiration=None,
    ):
        """
        bot: Gedis chatbot object from chatflow
        reservation: reservation object from schema
        ip_range: ip range for network eg: "10.70.0.0/16"
        node: list of node objects from explorer

        return reservation (Object) , config of network (dict)
        """
        if not interactive and noninteractive_args:
            network_name = noninteractive_args["name"]
        else:
            network_name = bot.string_ask(
                "Please add a network name. please remember it for next time. Otherwise leave it empty for using a generated name"
            )
        network = j.sal.zosv2.network.create(reservation, ip_range, network_name)
        network_config = self._register_network(
            bot,
            reservation,
            ip_range,
            network,
            nodes,
            customer_tid,
            ip_version,
            number_of_ipaddresses,
            interactive=interactive,
            noninteractive_args=noninteractive_args,
            expiration=expiration,
        )
        return reservation, network_config

    def _register_network(
        self,
        bot,
        reservation,
        ip_range,
        network,
        nodes,
        customer_tid,
        ip_version="IPv4",
        number_of_ipaddresses=0,
        interactive=True,
        noninteractive_args=None,
        expiration=None,
    ):
        """
        bot: Gedis chatbot object from chatflow
        reservation: reservation object from schema
        ip_range: ip range for network eg: "10.70.0.0/16"
        network: network object from schema
        node: list of node objects from explorer

        return config of network (dict)
        """
        number_of_ipaddresses = number_of_ipaddresses or len(nodes)
        ipv4 = ip_version == "IPv4"
        network_range = netaddr.IPNetwork(ip_range).ip

        if not interactive:
            network_config = noninteractive_args
            ip_addresses = network_config["ip_addresses"]
        else:
            network_config = dict()
            ip_addresses = list()

        for i, node_selected in enumerate(nodes):
            network_range += 256
            network_node = str(network_range) + "/24"
            if interactive:
                available_ips = self.get_all_ips(network_node)
                string_ips = []
                for ip in available_ips:
                    string_ips.append(ip.format())
                if number_of_ipaddresses > 0:
                    # user chooses the ip to be used for the node
                    ip_address = bot.drop_down_choice(f"Please choose the ip address {i+1}", string_ips)
                    ip_addresses.append(
                        ip_address
                    )  # ip in position i, corresponds to the node in position i in nodes_selected
                    string_ips.remove(ip_address)
                    number_of_ipaddresses -= 1
            j.sal.zosv2.network.add_node(network, node_selected.node_id, network_node)

        access_nodes = j.sal.zosv2.nodes_finder.nodes_search(farm_id=71)

        if ipv4:
            for node in filter(j.sal.zosv2.nodes_finder.filter_public_ip4, access_nodes):
                access_node = node
        else:
            for node in filter(j.sal.zosv2.nodes_finder.filter_public_ip6, access_nodes):
                access_node = node

        network_range += 256
        network_node = str(network_range) + "/24"
        j.sal.zosv2.network.add_node(network, access_node.node_id, network_node)

        network_range += 256
        network_node = str(network_range) + "/24"
        wg_quick = j.sal.zosv2.network.add_access(network, access_node.node_id, network_node, ipv4=True)

        network_config["name"] = network.name
        network_config["ip_addresses"] = ip_addresses
        network_config["wg"] = wg_quick
        j.sal.fs.writeFile(f"/sandbox/cfg/wireguard/{network.name}.conf", f"{wg_quick}")

        # register the reservation
        expiration = expiration or j.data.time.epoch + (60 * 60 * 24)
        rid = self.reservation_register(reservation, expiration, customer_tid)

        network_config["rid"] = rid

        return network_config

    def reservation_register(self, reservation, expiration, customer_tid):
        rid = j.sal.zosv2.reservation_register(reservation, expiration, customer_tid=customer_tid)

        if j.core.myenv.config.get("DEPLOYER") and customer_tid:
            # create a new object from deployed_reservation with the reservation and the tid
            deployed_rsv_model = j.clients.bcdbmodel.get(url="tfgrid.deployed_reservation.1", name="tfgrid_workloads")
            deployed_reservation = deployed_rsv_model.new()
            deployed_reservation.reservation_id = rid
            deployed_reservation.customer_tid = customer_tid
            deployed_reservation.save()
        return rid

    def reservation_failed(self, bot, category, resv_id):
        explorer = j.clients.explorer.explorer
        container_found = False
        trials = 50
        while not container_found:
            reservation_result = explorer.reservations.get(resv_id).results
            for result in reservation_result:
                if result.category == category:
                    container_found = True
            trials -= 1
            if trials == 0:
                break

        reservation = explorer.reservations.get(resv_id)
        failed = j.sal.zosv2.reservation_failed(reservation)
        if failed:
            res = f"# Sorry your reservation ```{resv_id}``` has failed :\n"
            for x in reservation.results:
                if x.state == "ERROR":
                    res += f"\n### {x.category}: ```{x.message}```\n"
            link = f"{explorer.url}/reservations/{resv_id}"
            res += f"<h2> <a href={link}>Full reservation info</a></h2>"
            res = j.tools.jinja2.template_render(text=res)
            bot.md_show(res)
        return failed

    def network_exists(self, tid):
        reservations = j.sal.zosv2.reservation_list(tid=tid)
        network_names = dict()
        names = set()
        for reservation in reservations:
            networks = reservation.data_reservation.networks
            expiration = reservation.data_reservation.expiration_provisioning

            for network in networks:
                if network.name not in names:
                    names.add(network.name)
                    network_name = network.name + " - end at: " + j.data.time.epoch2HRDateTime(expiration, local=True)
                    network_names[network_name] = network

        return network_names

    def add_node_to_network_exists(self, bot, reservation, nodes, network, expiration, customer_tid):
        network_resources = network.network_resources
        network_config = dict()
        list_ip_range = list()
        nodes_id = list()
        ip_addresses = list()
        ip_range_use = dict()

        # Get all ids of node
        for i, node_selected in enumerate(nodes):
            nodes_id.append(node_selected.node_id)

        # Check if any nodes selected is exist before in this network (to use IP range of this node not create new one)
        for network_resource in network_resources:
            if network_resource.node_id in nodes_id:
                ip_range_use[network_resource.node_id] = network_resource.iprange
            list_ip_range.append(network_resource.iprange)

        ip_range = network.iprange
        all_ranges = []

        # generate all free network Ip rnages of this network IP range
        network_range = netaddr.IPNetwork(ip_range).ip
        for i in range(1, 254):
            network_range += 256
            all_ranges.append(str(network_range) + "/24")
        used = set(list_ip_range)
        all_ip_range = set(all_ranges)
        free = all_ip_range - used

        for i, node_selected in enumerate(nodes):
            add_node = True
            # Check if node selected it's already exist in this network just create ip address
            if node_selected.node_id in list(ip_range_use.keys()):
                ip_range = netaddr.IPNetwork(ip_range_use[node_selected.node_id]).ip
                add_node = False
            # Check if node selected not exist in this network  generate new IP range sub of this network and add this node in network
            else:
                ip_range = random.choice(tuple(free))
                used.add(ip_range)
                free = all_ip_range - used

            if add_node:
                j.sal.zosv2.network.add_node(network, node_selected.node_id, ip_range)

            available_ips = self.get_all_ips(ip_range)
            string_ips = []
            for ip in available_ips:
                string_ips.append(ip.format())

            ip_address = bot.drop_down_choice(f"Please choose the ip address {i+1}", string_ips)
            ip_addresses.append(ip_address)

        reservation.data_reservation.networks.append(network._ddict)
        rid = self.reservation_register(reservation, expiration, customer_tid)

        network_config["rid"] = rid
        network_config["name"] = network.name
        network_config["ip_addresses"] = ip_addresses
        network_config["wg"] = j.sal.fs.readFile(f"/sandbox/cfg/wireguard/{network.name}.conf")
        return reservation, network_config

    def escrow_qr_show(self, bot, reservation_create_resp):
        # Get escrow info for reservation_create_resp dict
        escrow_info = j.sal.zosv2.reservation_escrow_information_with_qrcodes(reservation_create_resp)

        # view all qrcodes
        for i, escrow in enumerate(escrow_info):
            message_text = f"""
### escrow address :
{escrow['escrow_address']} \n
### amount to be paid :
{escrow['total_amount']}
"""
            msg = j.tools.jinja2.template_render(text=message_text)
            bot.qrcode_show(
                escrow["qrcode"],
                title=f"Scan the following with your application or enter the information below manually to proceed with payment #{i+1}",
                msg=msg,
                scale=4,
            )

    def save_reservation(self, rid, name, url):
        rsv_model = j.clients.bcdbmodel.get(url=url, name="tfgrid_solutions")
        reservation = rsv_model.new()
        reservation.rid = rid
        reservation.name = name
        reservation.save()

    def add_solution_name(self, bot, model):
        name_exists = False
        while not name_exists:
            solution_name = bot.string_ask("Please add a name for your solution")
            find = model.find(name=solution_name)
            if len(find) > 0:
                res = "# Please choose another name because this name already exist"
                res = j.tools.jinja2.template_render(text=res)
                bot.md_show(res)
            else:
                return solution_name
