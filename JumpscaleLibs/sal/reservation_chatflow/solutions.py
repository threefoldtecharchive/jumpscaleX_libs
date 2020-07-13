from Jumpscale import j
from collections import defaultdict


class ChatflowSolutions(j.baseclasses.object):
    __jslocation__ = "j.sal.chatflow_solutions"

    def list_network_solutions(self):
        networks = j.sal.chatflow_deployer.list_networks()
        result = []
        for n in networks:
            result.append(n.network_workloads[-1])
        return result

    def list_4to6gw_solutions(self):
        j.sal.chatflow_deployer.load_user_workloads()
        result = []
        for gateways in j.sal.chatflow_deployer.workloads["DEPLOY"]["GATEWAY4TO6"].values():
            result += gateways
        return result

    def list_delegated_domains(self):
        j.sal.chatflow_deployer.load_user_workloads()
        result = []
        for domains in j.sal.chatflow_deployer.workloads["DEPLOY"]["DOMAIN-DELEGATE"].values():
            result += domains
        return result

    def list_kubernetes_solutions(self):
        j.sal.chatflow_deployer.load_user_workloads()
        result = {}
        for kube_workloads in j.sal.chatflow_deployer.workloads["DEPLOY"]["KUBERNETES"].values():
            for workload in kube_workloads:
                if not isinstance(workload.metadata, dict):
                    continue
                if not workload.metadata.get("form_info"):
                    continue
                name = workload.metadata["form_info"].get("Solution name", workload.metadata.get("name"))
                if name:
                    result[f"{workload.info.pool_id}-{name}"] = workload
        return list(result.values())

    def list_ubuntu_solutions(self):
        j.sal.chatflow_deployer.load_user_workloads()
        result = []
        for container_workloads in j.sal.chatflow_deployer.workloads["DEPLOY"]["CONTAINER"].values():
            for workload in container_workloads:
                if not isinstance(workload.metadata, dict):
                    continue
                if not workload.metadata.get("form_info"):
                    continue
                if workload.metadata["form_info"].get("chatflow") == "ubuntu":
                    result.append(workload)
        return result

    def list_flist_solutions(self):
        j.sal.chatflow_deployer.load_user_workloads()
        result = []
        for container_workloads in j.sal.chatflow_deployer.workloads["DEPLOY"]["CONTAINER"].values():
            for workload in container_workloads:
                if not isinstance(workload.metadata, dict):
                    continue
                if not workload.metadata.get("form_info"):
                    continue
                if workload.metadata["form_info"].get("chatflow") == "flist":
                    result.append(workload)
        return result

    def list_gitea_solutions(self):
        j.sal.chatflow_deployer.load_user_workloads()
        result = []
        for container_workloads in j.sal.chatflow_deployer.workloads["DEPLOY"]["CONTAINER"].values():
            for workload in container_workloads:
                if not isinstance(workload.metadata, dict):
                    continue
                if not workload.metadata.get("form_info"):
                    continue
                if workload.metadata["form_info"].get("chatflow") == "gitea":
                    result.append(workload)
        return result

    def list_minio_solutions(self):
        j.sal.chatflow_deployer.load_user_workloads()
        result = {}
        for container_workloads in j.sal.chatflow_deployer.workloads["DEPLOY"]["CONTAINER"].values():
            for workload in container_workloads:
                if not isinstance(workload.metadata, dict):
                    continue
                if not workload.metadata.get("form_info"):
                    continue
                if workload.metadata["form_info"].get("chatflow") == "minio":
                    name = workload.metadata["form_info"].get("Solution name", workload.metadata.get("name"))
                    if name:
                        result[f"{workload.info.pool_id}-{name}"] = workload
        return list(result.keys())

    def list_exposed_solutions(self):
        j.sal.chatflow_deployer.load_user_workloads()
        result = []
        for proxies in j.sal.chatflow_deployer.workloads["DEPLOY"]["REVERSE-PROXY"].values():
            result += proxies
        return result
