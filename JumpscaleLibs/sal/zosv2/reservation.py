from .network import Network

_order = [
    "NETWORK_RESOURCE",
    "NETWORK",
    "ZDB",
    "VOLUME",
    "CONTAINER",
    "KUBERNETES",
    "DOMAIN-DELEGATE",
    "SUBDOMAIN",
    "PROXY",
    "REVERSE-PROXY",
    "GATEWAY4TO6",
]


class Reservation:
    def __init__(self):
        self._workloads = []

    @property
    def sorted(self):
        """
        return the list of workload sorted in the other they should be deployed on the node
        """
        return sorted(self.workloads, key=lambda w: _order.index(w.info.workload_type))

    def __repr__(self):
        per_type = {}
        for w in self.workloads:
            wt = str(w.info.workload_type)
            if wt not in per_type:
                per_type[wt] = []

            if wt == "NETWORK_RESOURCE":
                per_type[wt].extend(w.network_resources)
            else:
                per_type[wt].append(w)

        return str(per_type)

    def __str__(self):
        return str(per_type)
