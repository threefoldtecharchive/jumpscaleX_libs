from Jumpscale import j


class ResourceParser:
    def __init__(self, explorer, reservation):
        self._actor_directory = explorer.actors_get("tfgrid.directory")
        self._reservation = reservation

    def calculate_used_resources(self):
        resource_units_per_node = []

        workloads_per_nodes = self._workloads_per_node()
        for node_id, workloads in workloads_per_nodes.items():
            resource_units = ResourceUnitsNode(node_id=node_id)
            for _type, workload in workloads.items():
                if _type == "container":
                    for container in workload:
                        resource_units + self._process_container(container)
                elif _type == "zdb":
                    for zdb in workload:
                        resource_units + self._process_zdb(zdb)
                elif _type == "kubernetes":
                    for k8s in workload:
                        resource_units + self._process_kubernetes(k8s)
                elif _type == "volume":
                    for volume in workload:
                        resource_units + self._process_volume(volume)

            resource_units_per_node.append(resource_units)

        return resource_units_per_node

    def _workload_per_farm(self):
        """
        Separate individual workloads in a reservation based on the farm they are going to be deployed on
        """
        farmid_workload_map = {}
        wpn = self.workloads_per_node()
        for node_id in wpn:
            node = self._actor_directory.nodes.get(node_id, False)
            if node.farm_id not in farmid_workload_map:
                farmid_workload_map[node.farm_id] = self._workloads_dict()
            wl = farmid_workload_map[node.farm_id]
            for _typ in ["network", "zdb", "container", "volume", "kubernetes"]:
                wl[_typ] = [*wl[_typ], *self.workloads_per_node()[_typ]]

        return farmid_workload_map

    def _iterate_over_workloads(self):
        for _type in ["zdbs", "volumes", "containers", "networks"]:
            for workload in getattr(self._reservation.data_reservation, _type):
                yield _type[:-1], workload
        if hasattr(self._reservation.data_reservation, "kubernetes"):
            for workload in getattr(self._reservation.data_reservation, "kubernetes"):
                yield "kubernetes", workload

    def _workloads_dict(self):
        return {"network": [], "zdb": [], "volume": [], "container": [], "kubernetes": []}

    def _workloads_per_node(self):
        """
        Separate individual workloads in a reservation based on the farm they are going to be deployed on
        """
        mapping = {}

        for _typ, workload in self._iterate_over_workloads():
            if _typ == "network":
                for nr in workload.network_resources:
                    if not nr.node_id in mapping:
                        mapping[nr.node_id] = self._workloads_dict()
                    mapping[nr.node_id]["network"].append(nr)
            else:
                if not workload.node_id in mapping:
                    mapping[workload.node_id] = self._workloads_dict()
                mapping[workload.node_id][_typ].append(workload)

        return mapping

    def _process_volume(self, volume):
        if volume.type == "SSD":
            return ResourceUnitsNode(SRU=volume.size)
        elif volume.type == "HDD":
            return ResourceUnitsNode(HRU=volume.size)

    def _process_container(self, container):
        return ResourceUnitsNode(CRU=container.capacity.cpu, MRU=(container.capacity.memory / 1024))

    def _process_zdb(self, zdb):
        if zdb.disk_type == "SSD":
            return ResourceUnitsNode(SRU=zdb.size)
        elif zdb.disk_type == "HDD":
            return ResourceUnitsNode(HRU=zdb.size)

    def _process_kubernetes(self, k8s):
        if k8s.size == 1:
            return ResourceUnitsNode(CRU=1, MRU=2, SRU=50)
        elif k8s.size == 2:
            return ResourceUnitsNode(CRU=2, MRU=4, SRU=100)


class ResourceUnitsNode:
    def __init__(self, node_id=None, SRU=0, HRU=0, MRU=0, CRU=0):
        self.node_id = node_id
        self.SRU = SRU
        self.HRU = HRU
        self.MRU = MRU
        self.CRU = CRU

    def __add__(self, other):
        self.CRU += other.CRU
        self.HRU += other.HRU
        self.MRU += other.MRU
        self.SRU += other.SRU

    def __str__(self):
        return f"Total of resourceunits for node: {self.node_id} \n SRU: {self.SRU} \n CRU: {self.CRU} \n MRU: {self.MRU} \n HRU: {self.HRU}"

    def __repr__(self):
        return str(self)

