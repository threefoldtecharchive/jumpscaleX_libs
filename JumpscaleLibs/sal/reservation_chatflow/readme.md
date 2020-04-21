# Making use of reservation_chatflow

Reservation chatflow sal functions can be called from within a chatflow to help creating,registering, and parsing the result types to be used in the chatflow.

The tool is accessible through `j.sal.reservation_chatflow`

## Available functionalities

### Validate user

`validate_user(user_info)`

### Get available nodes

Get a list of nodes from the grid that are available where a filter can be applied on them based on the farm_id, farm_name, or any of the resource capacities (cru, sru, mru, or hru).

`nodes_get(number_of_nodes, farm_id=None, farm_name, cru, sru, mru, hru)`

where :

- *number_of_nodes*:  number of nodes to be returned

- *farm_id* : (optional) used to select nodes only from a specific farm with this id

- *farm_name* : (optional) used to select nodes only from specific farm with this name

- *cru* : (optional) nodes selected should have a minumum value of cru (core resource unit) equal to this

- *sru* : (optional) nodes selected should have a minumum value of sru (ssd resource unit) equal to this

- *mru* : (optional) nodes selected should have a minumum value of mru (memory resource unit) equal to this

- *hru* : (optional) nodes selected should have a minumum value of hru (hd resource unit) equal to this

### Select a network for deployment

View all networks created by the customer_tid given and let the user select on to be used in the reservation they are about to create/register in the solution chatflow

`network_select(bot, customer_tid)`

where:

- *bot*:  the chatbot instance from the chatflow

- *customer_tid*: the threebot id of the customer who created the networks that the same user will be selecting from.

### Get ip range

Get an ip range by interacting with the user in the chat bot. The user can either choose to input a custom ip range or they can get a generated ip range. The bot in the chatflow is passed for the interactive questions to appear in the same chatflow.

`ip_range_get(bot)`

where :

- *bot*:  the chatbot instance from the chatflow

### Create a network reservation

Create a new network reservation. The reservation object is passed as well as the network name and other parameters needed for the creation of the network. The ip_version provided (Ipv4 or Ipv6) indicates whether the connection to the network will be using which version.

The function updates the reservation object and returns a network_config dict where the dict has the following keys `["wg","rid"]`

`network_create(network_name, reservation, ip_range, customer_tid, ip_version, expiration)`

where :

- *network_name*: The name to create the network with. Should be unique.

- *reservation*:  the reservation instance where a new network will be added to. This is the reservation that will be registered

- *ip_range*: The ip range to create the network with in the form `{IP}/16`. example: `10.35.0.0/16`

- *customer_tid*:  the 3bot id of the user that is doing the reservation from the chatflow(the logged in user in the chatflow)

- *ip_version*:  ip version (Ipv4 or Ipv6) of the machine that will access the network later on

- *expiration*:  expiration of the network reservation

### Register any reservation

Register any reservation through the chatflow. This reservation could include anything such as a new network, container, kubernetes cluster, or zdb.  It returns the reservation id of the registered reservation

`reservation_register(reservation, expiration, customer_tid,expiration_provisioning)`

where :

- *reservation*: the reservation instance that will be registered.

- *expiration*:  expiration of the items in the reservation

- *customer_tid*:  the 3bot id of the user that is doing the reservation from the chatflow(the logged in user in the chatflow)

- *expiration_provisioning*: expiration of the registered reservation if not processed to next state(provisioned)




### Wait for reservation to succeed or expire

Wait for reservation results to be complete, have errors, or expire. If there are errors then error message is previewed in the chatflow to the user and the chat is ended.

`reservation_wait(bot, rid)`

where:

- *bot*: the chatbot instance from the chatflow

- *rid*: the reservation id of the reservation to check for results and wait on completion, failure or expiry.

### Check for reservation failure

Interactive check if the reservation failed in the category provided, then an error message will be shown to the user in the chatflow along with the error(s) causing the failure of the reservation.

`_reservation_failed(bot, reservation)`

where :

- *bot*:  the chatbot instance from the chatflow

- *resv_id*:  the reservation to be checked for its failure

### List networks for user

List all the networks currently in DEPLOY state created by the user having the threebot id (tid) given

`network_list(tid, reservations)`

where :

- *tid*: threebot id to filter network reservations on

- *reservations*: list of reservations to look for networks in. If not provided then `j.sal.zosv2.reservation_list(tid=tid,next_action="DEPLOY")` is used to get all reservations of that user and checking in them.

### Save reservation(solutions)

After reservation registration is complete, The corresponding reservation id, solution name, and all user options selected are saved in bcdb to keep track of all solutions deplloyed by the user and their names.

`reservation_save(rid, name, url, form_info=None)`

where :

- *rid*: reservation id of the deployed reservation

- *name*: unique solution name for the deployed solution

- *url*: url of the model corresponding to the solution chatflow used.

- *form_info*: dict containing all the user selections and inputs from the chat flow.

### Add solution name in chatflow

Continuosly asking the user for a solution name while checking if it already exists in the saved solutions for the specific chatflow. If it exists the user is prompted to enter a different name until a unique one is given.

`solution_name_add(bot, model)`

where:

- *bot*:  the chatbot instance from the chatflow

- *model*: the model of the schema of the speicific chatflow

### Get solutions

Get all solutions saved using the model corresponding to the given url.

`solutions_get(url):`

where:

- *url*: url of the schema to get all instances using it from bcdb

### Cancel reservation and delete solution from bcdb

Given url of the schema and a solution name, the solution is deleted and the corresponding reservation based on the solution's reservation id is canceled by the explorer.

`reservation_cancel_for_solution(url, solution_name):`

where:

- *url*: url of the schema to get all instances using it from bcdb

- *solution_name*: the name of the solution to be deleted and canceled

## Example

The following example includes usage of the tool in a chatflow in getting nodes, creating a network reservation, and a container reservation, then checking for its results to deploy an ubuntu container on a new network

```python3
from Jumpscale import j
import netaddr

def chat(bot):
    """
    """
    user_form_data = {}
    model = j.threebot.packages.tfgrid_solutions.tfgrid_solutions.bcdb_model_get("tfgrid.solutions.ubuntu.1")

    network = j.sal.reservation_chatflow.network_select(bot, CUSTOMER_TID)
    if not network:
        return

    user_form_data["Solution name"] = j.sal.reservation_chatflow.solution_name_add(bot, model)

    form = bot.new_form()
    cpu = form.int_ask("Please add how many CPU cores are needed", default=1)
    memory = form.int_ask("Please add the amount of memory in MB", default=1024)
    form.ask()
    user_form_data["CPU"] = cpu.value
    user_form_data["Memory"] = memory.value

    expirationdelta = int(bot.time_delta_ask("Please enter solution expiration time.", default="1d"))
    user_form_data["Solution expiration"] = j.data.time.secondsToHRDelta(expirationdelta)
    expiration = j.data.time.epoch + expirationdelta


    # Create new reservation
    reservation = j.sal.zosv2.reservation_create()

    # Get a node
    hru = math.ceil(memory.value / 1024)
    cru = cpu.value
    sru = 1  # needed space for a container is 250MiB
    nodes_selected = j.sal.reservation_chatflow.nodes_get(1, hru=hru, cru=cru, sru=sru)
    node_selected = nodes_selected[0]
    network.add_node(node_selected)
    ip_address = network.ask_ip_from_node(node_selected, "Please choose IP Address for your solution")
    user_form_data["IP Address"] = ip_address

    bot.md_show_confirm(user_form_data)
    network.update(identity.id)

    ip_address = config["ip_addresses"][0]
    network_name = config["name"]
    wg_config = config["wg"]

    container_flist = "https://hub.grid.tf/tf-bootable/ubuntu:18.04.flist"
    storage_url = "zdb://hub.grid.tf:9900"
    entry_point = "/bin/bash /start.sh"

    # create container and register the updated reservation
    j.sal.zosv2.container.create(
        reservation=reservation,
        node_id=node_selected.node_id,
        network_name=network.name,
        ip_address=ip_address,
        flist=container_flist,
        storage_url=storage_url,
        env={},
        interactive=False,
        entrypoint=entry_point,
        cpu=user_form_data["CPU"],
        public_ipv6=True,
        memory=user_form_data["Memory"],
    )
    resv_id = j.sal.reservation_chatflow.reservation_register(reservation, expiration, customer_tid=CUSTOMER_TID)

    # Check if reservation failed or not
    j.sal.reservation_chatflow.reservation_wait(bot, resv_id)
    j.sal.reservation_chatflow.reservation_save(
        resv_id, user_form_data["Solution name"], "tfgrid.solutions.ubuntu.1", user_form_data
    )

    res = f"""\
    # Ubuntu has been deployed successfully: your reservation id is: {resv_id}
    To connect ```ssh root@{ip_address}``` .It may take a few minutes.
    """
    bot.md_show(j.core.text.strip(res))

```
