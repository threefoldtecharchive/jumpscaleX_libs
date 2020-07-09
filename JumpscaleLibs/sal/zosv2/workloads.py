from Jumpscale import j
from .signature import sign_workload, sign_delete_request, sign_provision_request


class Workloads:
    def __init__(self, explorer):
        self._workloads = explorer.workloads

    def list(self, customer_tid=None, next_action=None):
        return self._workloads.list(customer_tid, next_action)

    def iter(self, customer_tid=None, next_action=None):
        return self._workloads.iter(customer_tid, next_action)

    def get(self, workload_id):
        return self._workloads.get(workload_id)

    def deploy(self, workload, identity=None):
        me = identity if identity else j.me
        workload.info.customer_tid = me.tid
        workload.info.workload_id = 1
        workload.info.epoch = j.data.time.epoch
        workload.info.next_action = "deploy"
        # allow user to delete the workload
        workload.info.signing_request_delete.signers = [1]
        workload.info.signing_request_delete.quorum_min = 1

        signature = sign_workload(workload, me.encryptor.signing_key)
        workload.info.customer_signature = j.data.hash.bin2hex(signature)
        print(workload.info.customer_signature)
        return self._workloads.create(workload)

    def decomission(self, workload_id, identity=None):
        me = identity if identity else j.me
        workload = self.get(workload_id)
        signature = sign_delete_request(workload, me.tid, me.encryptor.signing_key)
        return self._workloads.sign_delete(workload_id, me.tid, signature)
