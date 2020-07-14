from Jumpscale import j


class ChatflowSolutions(j.baseclasses.object):
    __jslocation__ = "j.sal.chatflow_solutions"

    def list_network_solutions(self, next_action="DEPLOY"):
        networks = j.sal.chatflow_deployer.list_networks(next_action=next_action)
        result = []
        for n in networks.values():
            result.append(n.network_workloads[-1])
        return result

    def list_4to6gw_solutions(self, next_action="DEPLOY"):
        j.sal.chatflow_deployer.load_user_workloads()
        result = []
        for gateways in j.sal.chatflow_deployer.workloads[next_action]["GATEWAY4TO6"].values():
            result += gateways
        return result

    def list_delegated_domains(self, next_action="DEPLOY"):
        j.sal.chatflow_deployer.load_user_workloads()
        result = []
        for domains in j.sal.chatflow_deployer.workloads[next_action]["DOMAIN-DELEGATE"].values():
            result += domains
        return result

    def list_kubernetes_solutions(self, next_action="DEPLOY"):
        j.sal.chatflow_deployer.load_user_workloads()
        result = {}
        for kube_workloads in j.sal.chatflow_deployer.workloads[next_action]["KUBERNETES"].values():
            for workload in kube_workloads:
                if not workload.metadata:
                    continue
                try:
                    metadata = j.data.serializers.json.loads(workload.metadata)
                except:
                    metadata = j.data.serializers.json.loads(
                        j.sal.chatflow_deployer.decrypt_metadata(workload.metadata)
                    )
                    if not metadata:
                        continue
                if not metadata.get("form_info"):
                    continue
                name = metadata["form_info"].get("Solution name", metadata.get("name"))
                if name:
                    if f"{workload.info.pool_id}-{name}" in result:
                        continue
                    result[f"{workload.info.pool_id}-{name}"] = workload
        return list(result.values())

    def list_ubuntu_solutions(self, next_action="DEPLOY"):
        j.sal.chatflow_deployer.load_user_workloads()
        result = []
        for container_workloads in j.sal.chatflow_deployer.workloads[next_action]["CONTAINER"].values():
            for workload in container_workloads:
                if not workload.metadata:
                    continue
                try:
                    metadata = j.data.serializers.json.loads(workload.metadata)
                except:
                    metadata = j.data.serializers.json.loads(
                        j.sal.chatflow_deployer.decrypt_metadata(workload.metadata)
                    )
                    if not metadata:
                        continue
                if not metadata.get("form_info"):
                    continue
                if metadata["form_info"].get("chatflow") == "ubuntu":
                    result.append(workload)
        return result

    def list_flist_solutions(self, next_action="DEPLOY"):
        j.sal.chatflow_deployer.load_user_workloads()
        result = []
        for container_workloads in j.sal.chatflow_deployer.workloads[next_action]["CONTAINER"].values():
            for workload in container_workloads:
                if not workload.metadata:
                    continue
                try:
                    metadata = j.data.serializers.json.loads(workload.metadata)
                except:
                    metadata = j.data.serializers.json.loads(
                        j.sal.chatflow_deployer.decrypt_metadata(workload.metadata)
                    )
                    if not metadata:
                        continue
                if not metadata.get("form_info"):
                    continue
                if metadata["form_info"].get("chatflow") == "flist":
                    result.append(workload)
        return result

    def list_gitea_solutions(self, next_action="DEPLOY"):
        j.sal.chatflow_deployer.load_user_workloads()
        result = []
        for container_workloads in j.sal.chatflow_deployer.workloads[next_action]["CONTAINER"].values():
            for workload in container_workloads:
                if not workload.metadata:
                    continue
                try:
                    metadata = j.data.serializers.json.loads(workload.metadata)
                except:
                    metadata = j.data.serializers.json.loads(
                        j.sal.chatflow_deployer.decrypt_metadata(workload.metadata)
                    )
                    if not metadata:
                        continue
                if not metadata.get("form_info"):
                    continue
                if metadata["form_info"].get("chatflow") == "gitea":
                    result.append(workload)
        return result

    def list_minio_solutions(self, next_action="DEPLOY"):
        j.sal.chatflow_deployer.load_user_workloads()
        result = {}
        for container_workloads in j.sal.chatflow_deployer.workloads[next_action]["CONTAINER"].values():
            for workload in container_workloads:
                if not workload.metadata:
                    continue
                try:
                    metadata = j.data.serializers.json.loads(workload.metadata)
                except:
                    metadata = j.data.serializers.json.loads(
                        j.sal.chatflow_deployer.decrypt_metadata(workload.metadata)
                    )
                    if not metadata:
                        continue
                if not metadata.get("form_info"):
                    continue
                if metadata["form_info"].get("chatflow") == "minio":
                    name = metadata["form_info"].get("Solution name", metadata.get("name"))
                    if name:
                        if f"{workload.info.pool_id}-{name}" in result:
                            continue
                        result[f"{workload.info.pool_id}-{name}"] = workload
        return list(result.keys())

    def list_exposed_solutions(self, next_action="DEPLOY"):
        j.sal.chatflow_deployer.load_user_workloads()
        result = []
        for proxies in j.sal.chatflow_deployer.workloads[next_action]["REVERSE-PROXY"].values():
            result += proxies
        return result

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
