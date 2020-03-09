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

    def network_configure(self, bot, reservation, node):
        """
        bot: Gedis chatbot object from chatflow
        reservation: reservation object from schema
        node: node object from explorer

        return reservation (Object) , config of network (dict)
        """
        ip_range = self.get_ip_range(bot)
        return self.get_network(bot, reservation, ip_range, node)

    def get_ip_range(self, bot):
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

    def get_network(self, bot, reservation, ip_range, node):
        """
        bot: Gedis chatbot object from chatflow
        reservation: reservation object from schema
        ip_range: ip range for network eg: "10.70.0.0/16"
        node: node object from explorer

        return reservation (Object) , config of network (dict)
        """
        network_choice = ["New network", "Existing network"]

        user_choice = bot.single_choice("Create a new network or use an existing one.", network_choice)
        if user_choice == "New network":
            network_name = bot.string_ask(
                "Please add a network name. Don't forget to save it. otherwise Leave empty for using a generated name"
            )
            network = j.sal.zosv2.network.create(reservation, ip_range, network_name)
            network_config = self._register_network(bot, reservation, ip_range, network, node)
        else:
            res = "# This feature is not available yet."
            res = j.tools.jinja2.template_render(text=res)
            bot.md_show(res)

        return reservation, network_config

    def _register_network(self, bot, reservation, ip_range, network, node):
        """
        bot: Gedis chatbot object from chatflow
        reservation: reservation object from schema
        ip_range: ip range for network eg: "10.70.0.0/16"
        network: network object from schema
        node: node object from explorer

        return config of network (dict)
        """
        network_config = dict()
        network_range = netaddr.IPNetwork(ip_range).ip
        network_range += 256
        network_node = str(network_range) + "/24"

        avaliable_ips = self.get_all_ips(network_node)
        string_ips = []
        for ip in avaliable_ips:
            string_ips.append(ip.format())

        ip_address = bot.drop_down_choice("Please choose ip address of the container", string_ips)
        network_config["ip_address"] = ip_address
        j.sal.zosv2.network.add_node(network, node.node_id, network_node)
        network_range += 256
        network_node = str(network_range) + "/24"

        wg_quick = j.sal.zosv2.network.add_access(network, node.node_id, network_node, ipv4=True)
        network_config["wg"] = wg_quick
        expiration = j.data.time.epoch + (3600 * 24 * 365)
        network_config["name"] = network.name

        # register the reservation
        j.sal.zosv2.reservation_register(reservation, expiration)

        return network_config
