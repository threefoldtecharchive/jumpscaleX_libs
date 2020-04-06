import netaddr
from Jumpscale import j
import random


class Chatflow(j.baseclasses.object):
    __jslocation__ = "j.sal.reservation_chatflow"

    def _init(self, **kwargs):
        j.data.bcdb.get("tfgrid_solutions")
        self._explorer = j.clients.explorer.default

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

    def validate_user(self, user_info):
        if not j.tools.threebot.with_threebotconnect:
            error_msg = """
            This chatflow is not supported when Threebot is in dev mode.
            To enable Threebot connect : `j.tools.threebot.threebotconnect_disable()`
            """
            raise j.exceptions.Runtime(error_msg)
        if not user_info["email"]:
            raise j.exceptions.Value("Email shouldn't be empty")
        if not user_info["username"]:
            raise j.exceptions.Value("Name of logged in user shouldn't be empty")
        return self._explorer.users.get(name=user_info["username"], email=user_info["email"])

    def nodes_get(self, number_of_nodes, farm_id=None, farm_name=None, cru=None, sru=None, mru=None, hru=None):
        # get nodes without public ips
        nodes = j.sal.zosv2.nodes_finder.nodes_by_capacity(
            farm_id=farm_id, farm_name=farm_name, cru=cru, sru=sru, mru=mru, hru=hru
        )  # Choose free farm

        # to avoid using the same node with different networks
        nodes = list(nodes)
        nodes_selected = []
        for i in range(number_of_nodes):
            node = random.choice(nodes)
            while not j.sal.zosv2.nodes_finder.filter_is_up(node) or node in nodes_selected:
                node = random.choice(nodes)
            nodes_selected.append(node)
        return nodes_selected

    def network_select(self, bot, customer_tid):
        networks = self.network_list(customer_tid)
        names = []
        for n in networks.keys():
            names.append(n)
        if not names:
            res = "<h2> You don't have any networks, please use the network chatflow to create one</h2>"
            res = j.tools.jinja2.template_render(text=res)
            bot.md_show(res)
            return None
        return networks[bot.single_choice("Choose a network", names)]

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

    def network_create(
        self, network_name, reservation, ip_range, customer_tid, ip_version, expiration=None,
    ):
        """
        bot: Gedis chatbot object from chatflow
        reservation: reservation object from schema
        ip_range: ip range for network eg: "10.70.0.0/16"
        node: list of node objects from explorer

        return reservation (Object) , config of network (dict)
        """
        network = j.sal.zosv2.network.create(reservation, ip_range, network_name)
        node_subnets = netaddr.IPNetwork(ip_range).subnet(24)
        network_config = dict()
        access_nodes = j.sal.zosv2.nodes_finder.nodes_search(farm_name="freefarm")
        use_ipv4 = ip_version == "IPv4"

        if use_ipv4:
            nodefilter = j.sal.zosv2.nodes_finder.filter_public_ip4
        else:
            nodefilter = j.sal.zosv2.nodes_finder.filter_public_ip6
        for node in filter(nodefilter, access_nodes):
            access_node = node
            break
        else:
            raise j.exceptions.NotFound("Could not find available access node")

        j.sal.zosv2.network.add_node(network, access_node.node_id, str(next(node_subnets)))
        wg_quick = j.sal.zosv2.network.add_access(network, access_node.node_id, str(next(node_subnets)), ipv4=use_ipv4)

        network_config["wg"] = wg_quick
        j.sal.fs.writeFile(f"/sandbox/cfg/wireguard/{network_name}.conf", f"{wg_quick}")

        # register the reservation
        expiration = expiration or j.data.time.epoch + (60 * 60 * 24)
        rid = self.reservation_register(reservation, expiration, customer_tid)

        network_config["rid"] = rid

        return network_config

    def reservation_register(self, reservation, expiration, customer_tid):
        rid = j.sal.zosv2.reservation_register(reservation, expiration, customer_tid=customer_tid)
        reservation.id = rid

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

    def network_list(self, tid):
        reservations = j.sal.zosv2.reservation_list(tid=tid, next_action="DEPLOY")
        network_names = dict()
        names = set()
        for reservation in sorted(reservations, key=lambda r: r.id, reverse=True):
            networks = reservation.data_reservation.networks
            expiration = reservation.data_reservation.expiration_reservation

            for network in networks:
                if network.name in names:
                    continue
                names.add(network.name)
                remaning = expiration - j.data.time.epoch
                network_name = (
                    network.name
                    + " - ends in: "
                    + j.data.time.secondsToHRDelta(remaning)
                )
                network.expiration = expiration
                network_names[network_name] = network

        return network_names

    def add_node_to_network(self, node, network, reservation=None):
        network_resources = network.network_resources
        used_ip_ranges = set()
        reservation = None

        used_networkrange = None
        for network_resource in network_resources:
            if network_resource.node_id == node.node_id:
                used_networkrange = network_resource.iprange
                break
            used_ip_ranges.add(network_resource.iprange)
            for peer in network_resource.peers:
                used_ip_ranges.add(peer.iprange)
        else:
            network_range = netaddr.IPNetwork(network.iprange)
            for idx, subnet in enumerate(network_range.subnet(24)):
                if str(subnet) not in used_ip_ranges:
                    break
            else:
                raise j.exceptions.Input("Failed to find free network")
            j.sal.zosv2.network.add_node(network, node.node_id, str(subnet))
            if reservation is None:
                reservation = j.sal.zosv2.reservation_create()
            else:
                for rnetwork in reservation.data_reservation.networks[:]:
                    if rnetwork.name == network.name:
                        reservation.data_reservation.networks.remove(rnetwork)
                        break
            reservation.data_reservation.networks.append(network._ddict)
            used_networkrange = str(subnet)
        return reservation, used_networkrange

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

    def reservation_save(self, rid, name, url):
        rsv_model = j.clients.bcdbmodel.get(url=url, name="tfgrid_solutions")
        reservation = rsv_model.new()
        reservation.rid = rid
        reservation.name = name
        reservation.save()

    def solution_name_add(self, bot, model):
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

    def solutions_get(self, url):
        model = j.clients.bcdbmodel.get(url=url, name="tfgrid_solutions")
        solutions = model.find()
        reservations = []
        explorer = j.clients.explorer.explorer

        for solution in solutions:
            reservation = explorer.reservations.get(solution.rid)
            reservations.append(reservation)
        return reservations

    def reservation_cancel_for_solution(self, url, solution_name):
        model = j.clients.bcdbmodel.get(url=url, name="tfgrid_solutions")
        solutions = model.find(name=solution_name)
        for solution in solutions:
            j.sal.zosv2.reservation_cancel(solution.rid)
            solution.delete()
