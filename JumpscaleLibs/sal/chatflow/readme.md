# Making use of reservation_chatflow

Reservation chatflow sal functions can be called from within a chatflow to help creating,registering, and parsing the result types to be used in the chatflow.

The tool is accessible through `j.sal.reservation_chatflow`

## Available functionalities

### Get available nodes

Get a list of nodes from the grid that are available where a filter can be applied on them based on the farm_id, farm_name, or any of the resource capacities (cru, sru, mru, or hru).

`nodes_get(number_of_nodes, ip_version, farm_id=None, farm_name, cru, sru, mru, hru)`

where :

- *number_of_nodes*:  number of nodes to be returned

- *ip_version*: ip version (Ipv4 or Ipv6) of the nodes to be returned

- *farm_id* : (optional) used to select nodes only from a specific farm with this id

- *farm_name* : (optional) used to select nodes only from specific farm with this name

- *cru* : (optional) nodes selected should have a minumum value of cru (core resource unit) equal to this

- *sru* : (optional) nodes selected should have a minumum value of sru (ssd resource unit) equal to this

- *mru* : (optional) nodes selected should have a minumum value of mru (memory resource unit) equal to this

- *hru* : (optional) nodes selected should have a minumum value of hru (hd resource unit) equal to this


### Get ip range

Get an ip range by interacting with the user in the chat bot. The user can either choose to input a custom ip range or they can get a generated ip range. The bot in the chatflow is passed for the interactive questions to appear in the same chatflow.

`ip_range_get(bot)`

where :

- *bot*:  the chatbot instance from the chatflow

### Get all IPs

Get a list possible ips for a machine given a valid ip range

`get_all_ips(ip_range)`

where :

- *ip_range*:  the ip range to generate ips from. example: \"10.70.0.0/16\"


### Configure and create/get a network reservation

Create or get(not implemented yet) a network reservation. When creating a new network, the data is provided and interactive questions for further information will be asked in the chatflow. When creating a new network the user will be also pass through the interactive questions of ip_range_get(bot). They will also be asked about an optional network name so that in the future reservations can be created on networks with the same name.

The function returns the updated reservation and a network_config dict where the dict has the following keys `["name","ip_addresses","wg","rid"]`

`network_configure(bot, reservation, nodes, customer_tid, ip_version, number_of_ipaddresses)`

where :

- *bot*:  the chatbot instance from the chatflow

- *reservation*:  the reservation instance where a new network will be added to. This is the reservation that will be registered

- *nodes*:  The list of nodes that will be added in the network when created

- *customer_tid*:  the 3bot id of the user that is doing the reservation from the chatflow(the logged in user in the chatflow)

- *ip_version*:  ip version (Ipv4 or Ipv6) of the machine that will access the results of the reservations later on

- *number_of_ipaddresses*: number of ip addresses that are to be returned from the reservation to create further reservations on such as container creation. **min=1, max=number of nodes**


### Register any reservation
Register any reservation through the chatflow. This reservation could include anything such as a new network, container, kubernetes cluster, or zdb.

`reservation_register(reservation, expiration, customer_tid)`

where :

- *reservation*: the reservation instance where a new network will be added to. This is the reservation that will be registered

- *expiration*:  expiration of the items in the reservation

- *customer_tid*:  the 3bot id of the user that is doing the reservation from the chatflow(the logged in user in the chatflow)

### Check for reservation failure
Interactive check if the reservation failed in the category provided, then an error message will be shown to the user in the chatflow along with the error(s) causing the failure of the reservation.

`reservation_failed(bot, category, resv_id)`

where :

- *bot*:  the chatbot instance from the chatflow

- *category*:  category to check for in the result of the reservation. example \"CONTAINER\", \"Network\", or \"ZDB\"

- *resv_id*:  the reservation id of the reservation to be checked for its results


## Example
The following example includes usage of the tool in a chatflow in getting nodes, creating a network reservation, and a container reservation, then checking for its results to deploy an ubuntu container on a new network

```python3
from Jumpscale import j
import netaddr

def chat(bot):
    """
    """

    expiration = j.data.time.epoch + (60 * 60 * 24)  # for one day
    explorer = j.clients.explorer.explorer

    # Create new reservation
    reservation = j.sal.zosv2.reservation_create()

    # Get a node
    ip_version = "IPv4"
    nodes_selected = j.sal.reservation_chatflow.nodes_get(1, ip_version=ip_version)
    node_selected = nodes_selected[0]

    # Configure and create network
    reservation, config = j.sal.reservation_chatflow.network_configure(
        bot, reservation, [node_selected], customer_tid=CUSTOMER_TID, ip_version=ip_version
    )

    ip_address = config["ip_addresses"][0]
    network_name = config["name"]
    wg_config = config["wg"]

    container_flist = "https://hub.grid.tf/tf-bootable/ubuntu:18.04.flist"
    storage_url = "zdb://hub.grid.tf:9900"

    # create container and register the updated reservation
    cont = j.sal.zosv2.container.create(
        reservation=reservation,
        node_id=node_selected.node_id,
        network_name=network_name,
        ip_address=ip_address,
        flist=container_flist,
        storage_url=storage_url,
        env={},
        interactive=True,
    )

    resv_id = j.sal.reservation_chatflow.reservation_register(reservation, expiration, customer_tid=CUSTOMER_TID)

    # Check if reservation failed or not
    if j.sal.reservation_chatflow.reservation_failed(bot=bot, category="CONTAINER", resv_id=resv_id):
        return

    else:

        res = f"# Ubuntu has been deployed successfully: your reservation id is: {resv_id} "

        bot.md_show(res)

        filename = "{}_{}.conf".format(name, resv_id)

        res = """
                # Use the following template to configure your wireguard connection. This will give you access to your 3bot.
                ## Make sure you have <a href="https://www.wireguard.com/install/">wireguard</a> installed:
                ## ```wg-quick up /etc/wireguard/{}```
                Click next
                to download your configuration
                """.format(
            filename
        )
        res = j.tools.jinja2.template_render(text=j.core.text.strip(res), **locals())
        bot.md_show(res)

        res = j.tools.jinja2.template_render(text=wg_config, **locals())
        bot.download_file(res, filename)

        res = "# Open your browser at ```{}:7681``` It may take a few minutes.".format(ip_address)
        res = j.tools.jinja2.template_render(text=res, **locals())
        bot.md_show(res)

```
