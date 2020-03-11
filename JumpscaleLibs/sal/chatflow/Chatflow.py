import netaddr
from Jumpscale import j
import random


class Chatflow(j.baseclasses.object):
    __jslocation__ = "j.sal.chatflow"

    def _init(self, **kwargs):
        pass

    def get_all_ips(self, ip_range):
        """
        ip_range: (String)ip range of network
        return all available ips of this network
        """
        networks = netaddr.IPNetwork(ip_range)
        ips = []
        for ip in list(networks.iter_hosts()):
            ips.append(ip.format())
        return ips

    def nodes_get(self, number_of_nodes, ip_version):
        nodes = j.sal.zosv2.nodes_finder.nodes_search()
        nodes_selected = list()
        if ip_version == "IPV4":
            for node in filter(j.sal.zosv2.nodes_finder.filter_public_ip4, nodes):
                if len(nodes_selected) < number_of_nodes:
                    nodes_selected.append(node)
        else:
            for node in filter(j.sal.zosv2.nodes_finder.filter_public_ip6, nodes):
                if len(nodes_selected) < number_of_nodes:
                    nodes_selected.append(node)

        return nodes_selected

    def network_configure(self, bot, reservation, nodes):
        """
        bot: Gedis chatbot object from chatflow
        reservation: reservation object from schema
        node: list of node objects from explorer

        return reservation (Object) , config of network (dict)
        """
        ip_range = self.ip_range_get(bot)
        return self.network_get(bot, reservation, ip_range, nodes)

    def ip_range_get(self, bot):
        """
        bot: Gedis chatbot object from chatflow
        return ip_range from user or generated one
        """
        ip_range_choose = ["Specify IP Range", "Choose IP Range for me"]
        iprange_user_choice = bot.single_choice("Specify IP Range OR Choose IP Range for me?", ip_range_choose)
        if iprange_user_choice == "Specify IP Range":
            ip_range = bot.string_ask("Please add private IP Range of the network")
        else:
            first_digit = random.choice([192, 172, 10])
            if first_digit == 10:
                second_digit = random.randint(0, 255)
            elif first_digit == 172:
                second_digit = random.randint(16, 31)
            else:
                second_digit = 168
            ip_range = str(first_digit) + "." + str(second_digit) + ".0.0/16"
        return ip_range

    def network_get(self, bot, reservation, ip_range, nodes):
        """
        bot: Gedis chatbot object from chatflow
        reservation: reservation object from schema
        ip_range: ip range for network eg: "10.70.0.0/16"
        node: list of node objects from explorer

        return reservation (Object) , config of network (dict)
        """
        network_choice = ["New network", "Existing network"]

        user_choice = bot.single_choice("Create a new network or use an existing one.", network_choice)
        if user_choice == "New network":
            network_name = bot.string_ask(
                "Please add a network name. Don't forget to save it. Otherwise leave it empty for using a generated name"
            )
            network = j.sal.zosv2.network.create(reservation, ip_range, network_name)
            network_config = self._register_network(bot, reservation, ip_range, network, nodes)
        else:
            res = "# This feature is not available yet."
            res = j.tools.jinja2.template_render(text=res)
            bot.md_show(res)

        return reservation, network_config

    def _register_network(self, bot, reservation, ip_range, network, nodes):
        """
        bot: Gedis chatbot object from chatflow
        reservation: reservation object from schema
        ip_range: ip range for network eg: "10.70.0.0/16"
        network: network object from schema
        node: list of node objects from explorer

        return config of network (dict)
        """
        network_config = dict()
        network_range = netaddr.IPNetwork(ip_range).ip

        ip_addresses = list()

        for i, node_selected in enumerate(nodes):
            network_range += 256
            network_node = str(network_range) + "/24"

            avaliable_ips = self.get_all_ips(network_node)
            string_ips = []
            for ip in avaliable_ips:
                string_ips.append(ip.format())

            # user chooses the ip to be used for the node
            ip_address = bot.drop_down_choice(f"Please choose the ip address of node {i+1}", string_ips)
            ip_addresses.append(ip_address)  # ip in position i, corresponds to the node in position i in nodes_selected
            string_ips.remove(ip_address)

            j.sal.zosv2.network.add_node(network, node_selected.node_id, network_node)
            network_range += 256
            network_node = str(network_range) + "/24"

            wg_quick = j.sal.zosv2.network.add_access(network, node_selected.node_id, network_node, ipv4=True)

        network_config["name"] = network.name
        network_config["ip_addresses"] = ip_addresses
        network_config["wg"] = wg_quick

        # register the reservation
        expiration = j.data.time.epoch + (3600 * 24 * 365)
        j.sal.zosv2.reservation_register(reservation, expiration)

        return network_config
