from Jumpscale import j


class Pools:
    def __init__(self, explorer):
        self._model_create = j.data.schema.get_from_url("tfgrid.workloads.pool.created.1")
        self._pools = explorer.pools
        self._farms = explorer.farms
        self._nodes = explorer.nodes
        self._gateways = explorer.gateway

    def _reserve(self, pool, identity=None):
        me = identity if identity else j.me

        pool.customer_tid = me.tid
        pool.json = pool.data_reservation._json
        pool.customer_signature = me.encryptor.sign_hex(pool.json.encode())

        return self._pools.create(pool)

    def create(self, cu, su, farm, currencies=None, identity=None):
        """
        create a new capacity pool

        :param cu: Amount of compute unit/sec to reserve
        :type cu: int
        :param su: Amount of storage unit/sec to reserve
        :type su: int
        :param farm: farm ID where to reserve the capacity
        :type farm: int or str
        :param currencies: list of currency accepted for payment, defaults to ["TFT"]
        :type currencies: list, optional
        :type identity: Jumpscale.tools.threebot.ThreebotMe.ThreebotMe
        :return: true if the reservation has been cancelled successfully
        :return: payment information
        :rtype: tfgrid.workloads.pool.created.1
        """
        if not currencies:
            currencies = ["TFT"]

        farm_id = farm
        if isinstance(farm, str):
            farm = self._farms.get(farm_name=farm)
            farm_id = farm.id

        node_ids = []
        for node in self._nodes.iter(farm_id=farm_id):
            node_ids.append(node.node_id)

        for gw in self._gateways.iter(farm_id=farm_id):
            node_ids.append(gw.node_id)

        pool = self._pools.new()
        pool.data_reservation.pool_id = 0
        pool.data_reservation.cus = cu
        pool.data_reservation.sus = su
        pool.data_reservation.node_ids = node_ids
        pool.data_reservation.currencies = currencies

        return self._reserve(pool, identity=identity)

    def extend(self, pool_id, cu, su, node_ids=None, currencies=None, identity=None):
        """
        Extend an existing capacity pool

        You can extend the amount of cloud units reserved as well as the list of nodes
        usable for this pool

        :param cu: Amount of compute unit/sec to add to the existing pool
        :type cu: int
        :param su: Amount of storage unit/sec to add to the existing pool
        :type su: int
        :param node_ids: if not None, the list of nodes IDs to link to the pool.
        :type farm: list of str
        :param currencies: list of currency accepted for payment, defaults to ["TFT"]
        :type currencies: list, optional
        :type identity: Jumpscale.tools.threebot.ThreebotMe.ThreebotMe
        :return: true if the reservation has been cancelled successfully
        :return: payment information
        :rtype: tfgrid.workloads.pool.created.1
        """
        p = self.get(pool_id)

        if not currencies:
            currencies = ["TFT"]

        pool = self._pools.new()
        pool.data_reservation.pool_id = p.pool_id
        pool.data_reservation.cus = p.cus + cu
        pool.data_reservation.sus = p.sus + su
        pool.data_reservation.node_ids = p.node_ids
        pool.data_reservation.currencies = currencies

        return self._reserve(pool, identity=identity)

    def get(self, pool_id):
        """
        return the detail of an existing capacity pool

        :param pool_id: pool ID
        :type pool_id: int
        :return: capacity pool
        :rtype: Pool
        """
        return self._pools.get(pool_id)

    def iter(self):
        """
        return an iterator that will yield all the
        capacity pool own by the current user
        """
        return self._pools.iter()

    def list(self, page=None):
        """
        list all the capacity pool own by the current user
        """
        return self._pools.list()
