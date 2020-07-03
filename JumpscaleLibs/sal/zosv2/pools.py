from Jumpscale import j


class Pools:
    def __init__(self, explorer):
        self._model_create = j.data.schema.get_from_url("tfgrid.workloads.pool.created.1")
        self._pools = explorer.pools
        self._farms = explorer.farms
        self._nodes = explorer.nodes

    def create(self, cu, su, farm, identity=None, expiration_provisioning=None, currencies=["TFT"]):
        me = identity if identity else j.me

        farm_id = farm
        if isinstance(farm, str):
            farm = self._farms.get(farm_name=farm)
            farm_id = farm.id

        node_ids = []
        for node in self._nodes.iter(farm_id=farm_id):
            node_ids.append(node.node_id)

        pool = self._pools.new()
        pool.customer_tid = me.tid
        pool.data_reservation.pool_id = 0
        pool.data_reservation.cus = cu
        pool.data_reservation.sus = su
        pool.data_reservation.node_ids = node_ids
        pool.data_reservation.currencies = currencies

        pool.json = pool.data_reservation._json
        print(pool)
        pool.customer_signature = me.encryptor.sign_hex(pool.json.encode())

        return self._pools.create(pool)

    def extend(self, pool_id, cu, su, identity=None):
        pass

    def iter(self):
        return self._pools.iter()

    def list(self, page=None):
        return self._pools.list()
