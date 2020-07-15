from Jumpscale import j


class ChatflowSolutions(j.baseclasses.object):
    __jslocation__ = "j.sal.chatflow_solutions"

    def list_network_solutions(self, next_action="DEPLOY"):
        networks = j.sal.chatflow_deployer.list_networks(next_action=next_action)
        result = []
        for n in networks.values():
            result.append(
                {
                    "Name": n.name,
                    "type": "network",
                    "IP Range": n.network_workloads[-1].network_iprange,
                    "Pool": n.network_workloads[-1].info.pool_id,
                    "nodes": {res.info.node_id: res.iprange for res in n.network_workloads},
                    "wids": [res.id for res in n.network_workloads],
                }
            )
        return result

    def list_4to6gw_solutions(self, next_action="DEPLOY"):
        j.sal.chatflow_deployer.load_user_workloads()
        result = []
        for gateways in j.sal.chatflow_deployer.workloads[next_action]["GATEWAY4TO6"].values():
            for g in gateways:
                result.append(
                    {
                        "wids": [g.id],
                        "Name": g.public_key,
                        "Public Key": g.public_key,
                        "Gateway": g.info.node_id,
                        "Pool": g.info.pool_id,
                    }
                )
        return result

    def list_delegated_domains(self, next_action="DEPLOY"):
        j.sal.chatflow_deployer.load_user_workloads()
        result = []
        for domains in j.sal.chatflow_deployer.workloads[next_action]["DOMAIN-DELEGATE"].values():
            for dom in domains:
                result.append(
                    {"wids": [dom.id], "Name": dom.domain, "Gateway": dom.info.node_id, "Pool": dom.info.pool_id}
                )
        return result

    def list_kubernetes_solutions(self, next_action="DEPLOY"):
        j.sal.chatflow_deployer.load_user_workloads()
        result = {}
        for kube_workloads in j.sal.chatflow_deployer.workloads[next_action]["KUBERNETES"].values():
            for workload in kube_workloads:
                if not workload.info.metadata:
                    continue
                try:
                    metadata = j.data.serializers.json.loads(workload.info.metadata)
                except:
                    metadata = j.data.serializers.json.loads(
                        j.sal.chatflow_deployer.decrypt_metadata(workload.info.metadata)
                    )
                    if not metadata:
                        continue
                if not metadata.get("form_info"):
                    continue
                name = metadata["form_info"].get("Solution name", metadata.get("name"))
                if name:
                    if f"{workload.info.pool_id}-{name}" in result:
                        if len(workload.master_ips != 0):
                            result[f"{workload.info.pool_id}-{name}"]["wids"].append(workload.id)
                            result[f"{workload.info.pool_id}-{name}"]["Slave IPs"].append(workload.ipaddress)
                        continue
                    result[f"{workload.info.pool_id}-{name}"] = {
                        "wids": [workload.id],
                        "Name": name,
                        "Master IP": workload.ipaddress if len(workload.master_ips) == 0 else workload.master_ips[0],
                        "Slave IPs": [],
                        "Pool": workload.info.pool_id,
                    }
                    if len(workload.master_ips != 0):
                        result[f"{workload.info.pool_id}-{name}"]["Slave IPs"].append(workload.ipaddress)
        return list(result.values())

    def list_ubuntu_solutions(self, next_action="DEPLOY"):
        j.sal.chatflow_deployer.load_user_workloads()
        result = []
        for container_workloads in j.sal.chatflow_deployer.workloads[next_action]["CONTAINER"].values():
            for workload in container_workloads:
                if not workload.info.metadata:
                    continue
                try:
                    metadata = j.data.serializers.json.loads(workload.info.metadata)
                except:
                    metadata = j.data.serializers.json.loads(
                        j.sal.chatflow_deployer.decrypt_metadata(workload.info.metadata)
                    )
                    if not metadata:
                        continue
                if not metadata.get("form_info"):
                    continue
                if metadata["form_info"].get("chatflow") == "ubuntu":
                    result.append(
                        {
                            "wids": [workload.id],
                            "Name": metadata.get("name", metadata["form_info"].get("Solution name")),
                            "IP Address": workload.network_connection[0].ipaddress,
                            "Network": workload.network_connection[0].network_id,
                            "Node": workload.info.node_id,
                            "Pool": workload.info.pool_id,
                        }
                    )
        return result

    def list_flist_solutions(self, next_action="DEPLOY"):
        j.sal.chatflow_deployer.load_user_workloads()
        result = []
        for container_workloads in j.sal.chatflow_deployer.workloads[next_action]["CONTAINER"].values():
            for workload in container_workloads:
                if not workload.info.metadata:
                    continue
                try:
                    metadata = j.data.serializers.json.loads(workload.info.metadata)
                except:
                    metadata = j.data.serializers.json.loads(
                        j.sal.chatflow_deployer.decrypt_metadata(workload.info.metadata)
                    )
                    if not metadata:
                        continue
                if not metadata.get("form_info"):
                    continue
                if metadata["form_info"].get("chatflow") == "flist":
                    result.append(
                        {
                            "wids": [workload.id],
                            "Name": metadata.get("name", metadata["form_info"].get("Solution name")),
                            "IP Address": workload.network_connection[0].ipaddress,
                            "Network": workload.network_connection[0].network_id,
                            "Node": workload.info.node_id,
                            "Pool": workload.info.pool_id,
                        }
                    )
        return result

    def list_gitea_solutions(self, next_action="DEPLOY"):
        j.sal.chatflow_deployer.load_user_workloads()
        result = []
        for container_workloads in j.sal.chatflow_deployer.workloads[next_action]["CONTAINER"].values():
            for workload in container_workloads:
                if not workload.info.metadata:
                    continue
                try:
                    metadata = j.data.serializers.json.loads(workload.info.metadata)
                except:
                    metadata = j.data.serializers.json.loads(
                        j.sal.chatflow_deployer.decrypt_metadata(workload.info.metadata)
                    )
                    if not metadata:
                        continue
                if not metadata.get("form_info"):
                    continue
                if metadata["form_info"].get("chatflow") == "gitea":
                    result.append(
                        {
                            "wids": [workload.id],
                            "Name": metadata.get("name", metadata["form_info"].get("Solution name")),
                            "IP Address": workload.network_connection[0].ipaddress,
                            "Network": workload.network_connection[0].network_id,
                            "Node": workload.info.node_id,
                            "Pool": workload.info.pool_id,
                        }
                    )
        return result

    def list_minio_solutions(self, next_action="DEPLOY"):
        # TODO: add related ZDB wids to solution dict
        j.sal.chatflow_deployer.load_user_workloads()
        result = {}
        for container_workloads in j.sal.chatflow_deployer.workloads[next_action]["CONTAINER"].values():
            for workload in container_workloads:
                if not workload.info.metadata:
                    continue
                try:
                    metadata = j.data.serializers.json.loads(workload.info.metadata)
                except:
                    metadata = j.data.serializers.json.loads(
                        j.sal.chatflow_deployer.decrypt_metadata(workload.info.metadata)
                    )
                    if not metadata:
                        continue
                if not metadata.get("form_info"):
                    continue
                if metadata["form_info"].get("chatflow") == "minio":
                    name = metadata["form_info"].get("Solution name", metadata.get("name"))
                    if name:
                        if f"{workload.info.pool_id}-{name}" in result:
                            result[f"{workload.info.pool_id}-{name}"]["wids"].append(workload.id)
                            result[f"{workload.info.pool_id}-{name}"]["Secondary IP"] = workload.network_connection[
                                0
                            ].ipaddress
                            result[f"{workload.info.pool_id}-{name}"]["Secondary Node"] = workload.network_connection[
                                0
                            ].ipaddress
                            continue
                        result[f"{workload.info.pool_id}-{name}"] = {
                            "wids": [workload.id],
                            "Name": name,
                            "Network": workload.network_connection[0].network_id,
                            "Primary IP": workload.network_connection[0].ipaddress,
                            "Primary Node": workload.info.node_id,
                            "Pool": workload.info.pool_id,
                        }
        return list(result.keys())

    def list_exposed_solutions(self, next_action="DEPLOY"):
        j.sal.chatflow_deployer.load_user_workloads()
        result = {}
        pools = set()
        name_to_proxy = {}
        for proxies in j.sal.chatflow_deployer.workloads[next_action]["REVERSE-PROXY"].values():
            for proxy in proxies:
                result[f"{proxy.info.pool_id}-{proxy.domain}"] = {
                    "wids": [proxy.id],
                    "Name": proxy.domain,
                    "Gateway": proxy.info.node_id,
                    "Pool": proxy.info.pool_id,
                }
                if proxy.info.metadata:
                    try:
                        metadata = j.data.serializers.json.loads(proxy.info.metadata)
                    except:
                        metadata = j.data.serializers.json.loads(
                            j.sal.chatflow_deployer.decrypt_metadata(proxy.info.metadata)
                        )
                        if not metadata:
                            continue
                    name = metadata.get("Solution name", metadata.get("form_info", {}).get("Solution name"))
                    if name:
                        result[f"{proxy.info.pool_id}-{proxy.domain}"]["Solution name"] = name
                        name_to_proxy[f"{proxy.info.pool_id}-{name}"] = proxy.domain
                pools.add(proxy.info.pool_id)

        # link tcp router containers to proxy reservations
        for pool_id in pools:
            for container_workload in j.sal.chatflow_deployer.workloads[next_action]["CONTAINER"][pool_id]:
                if (
                    container_workload.flist != "https://hub.grid.tf/tf-official-apps/tcprouter:latest.flist"
                    or not container_workload.info.metadata
                ):
                    continue
                try:
                    metadata = j.data.serializers.json.loads(container_workload.info.metadata)
                except:
                    metadata = j.data.serializers.json.loads(
                        j.sal.chatflow_deployer.decrypt_metadata(container_workload.info.metadata)
                    )
                    if not metadata:
                        continue
                solution_name = metadata.get(
                    "Solution name", metadata.get("name", metadata.get("form_info", {}).get("Solution name"))
                )
                if not solution_name:
                    continue
                if name_to_proxy.get(f"{pool_id}-{solution_name}"):
                    domain = name_to_proxy.get(f"{pool_id}-{solution_name}")
                    result[f"{pool_id}-{domain}"]["wids"].append(container_workload.id)
        return list(result.values())

    def cancel_solution(self, solution_wids):
        for wid in solution_wids:
            j.sal.zosv2.workloads.decomission(wid)

    def get_solution_ip_expose(self, workload):
        ip_address = None
        if workload.info.workload_type == "CONTAINER":
            ip_address = workload.network_connection[0].ipaddress
        elif workload.info.workload_type == "KUBERNETES":
            ip_address = workload.ipaddress
            if workload.master_ips:
                ip_address = workload.master_ips[0]
        return ip_address

    def get_solution_network_name(self, workload):
        network_name = None
        if workload.info.workload_type == "CONTAINER":
            network_name = workload.network_connection[0].network_id
        elif workload.info.workload_type == "KUBERNETES":
            network_name = workload.network_id
        return network_name
