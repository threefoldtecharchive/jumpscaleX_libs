from .id import _next_workload_id
from Jumpscale import j
from .signature import sign_workload


class Workloads:
    def __init__(self, explorer):
        self._workloads = explorer.workloads

    def list(self, node_id, customer_tid=None, next_action=None):
        return self._workloads.list(node_id, customer_tid, next_action)

    def iter(self, node_id, customer_tid=None, next_action=None):
        return self._workloads.iter(node_id, customer_tid, next_action)

    def get(self, workload_id):
        return self._workloads.get(workload_id)

    def deploy(self, workload, pool_id, identity=None):
        me = identity if identity else j.me
        workload.info.customer_tid = me.tid
        workload.info.workload_id = 1
        workload.info.pool_id = pool_id
        workload.info.epoch = j.data.time.epoch
        workload.info.expiration_provisioning = workload.info.epoch + (5 * 60)
        workload.info.next_action = "deploy"
        # allow user to delete the workload
        workload.info.signing_request_delete.signers = [1]
        workload.info.signing_request_delete.quorum_min = 1

        signature = sign_workload(workload, me.encryptor.signing_key)
        workload.info.customer_signature = j.data.hash.bin2hex(signature)
        print(workload.info.customer_signature)
        self._workloads.create(workload)
