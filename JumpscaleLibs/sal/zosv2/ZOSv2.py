import netaddr
from Jumpscale import j

from .container import ContainerGenerator
from .kubernetes import K8sGenerator
from .network import NetworkGenerator
from .node_finder import NodeFinder
from .volumes import VolumesGenerator
from .zdb import ZDBGenerator
from .billing import Billing
from .gateway import Gateway


class Zosv2(j.baseclasses.object):
    __jslocation__ = "j.sal.zosv2"

    def _init(self, **kwargs):
        self._explorer = j.clients.explorer.default
        self._nodes_finder = NodeFinder(self._explorer)
        self._network = NetworkGenerator(self._explorer)
        self._container = ContainerGenerator()
        self._volume = VolumesGenerator()
        self._zdb = ZDBGenerator(self._explorer)
        self._kubernetes = K8sGenerator(self._explorer)
        self._billing = Billing(self._explorer)
        self._gateway = Gateway(self._explorer)

    @property
    def network(self):
        return self._network

    @property
    def container(self):
        return self._container

    @property
    def volume(self):
        return self._volume

    @property
    def zdb(self):
        return self._zdb

    @property
    def kubernetes(self):
        return self._kubernetes

    @property
    def nodes_finder(self):
        return self._nodes_finder

    @property
    def billing(self):
        return self._billing

    def reservation_create(self):
        """
        creates a new empty reservation schema

        :return: reservation (tfgrid.workloads.reservation.1)
        :rtype: BCDBModel
        """
        return self._explorer.reservations.new()

    def reservation_register(
        self, reservation, expiration_date, identity=None, expiration_provisioning=None, customer_tid=None
    ):
        """
        register a reservation in BCDB

        :param reservation: reservation object
        :type reservation:  tfgrid.workloads.reservation.1
        :param expiration_date: timestamp of the date when to expiration should expire
        :type expiration_date: int
        :param identity: identity to use
        :type identity: Jumpscale.tools.threebot.ThreebotMe.ThreebotMe
        :param expiration_provisioning: timestamp of the date when to reservation should be provisionned
                                        if the reservation is not provisioning before this time, it will never be provionned
        :type expiration_provisioning: int, optional
        :return: reservation ID
        :rtype: int
        """
        me = identity if identity else j.tools.threebot.me.default
        reservation.customer_tid = me.tid

        if expiration_provisioning is None:
            expiration_provisioning = j.data.time.epoch + (3600 * 24 * 365)

        dr = reservation.data_reservation

        dr.expiration_provisioning = expiration_provisioning
        dr.expiration_reservation = expiration_date
        dr.signing_request_delete.quorum_min = 0
        dr.signing_request_provision.quorum_min = 0

        # make the reservation cancellable by the user that registered it
        dr.signing_request_delete.signers.append(me.tid)
        dr.signing_request_delete.quorum_min = len(dr.signing_request_delete.signers)

        reservation.json = dr._json
        reservation.customer_signature = me.nacl.sign_hex(reservation.json.encode())

        id = self._explorer.reservations.create(reservation)
        return id

    def reservation_accept(self, reservation, identity=None):
        """
        A farmer need to use this function to notify he accepts to deploy the reservation
        on his node

        :param reservation: reservation object
        :type reservation:  tfgrid.workloads.reservation.1
        :param identity: identity to use
        :type identity: Jumpscale.tools.threebot.ThreebotMe.ThreebotMe
        :return: returns true if not error,raise an exception otherwise
        :rtype: bool
        """
        me = identity if identity else j.tools.threebot.me.default

        reservation.json = reservation.data_reservation._json
        signature = me.nacl.sign_hex(reservation.json.encode())
        # TODO: missing sign_farm
        # return self._explorer.reservations.sign_farmer(reservation.id, me.tid, signature)

    def reservation_result(self, reservation_id):
        """
        returns the list of workload provisioning results of a reservation

        :param reservation_id: reservation ID
        :type reservation_id: int
        :return: list of tfgrid.workloads.reservation.result.1
        :rtype: list
        """
        return self.reservation_get(reservation_id).results

    def reservation_get(self, reservation_id):
        """
        fetch a specific reservation from BCDB

        :param reservation_id: reservation ID
        :type reservation_id: int
        :return: reservation object
        :rtype: "tfgrid.workloads.reservation.1
        """
        return self._explorer.reservations.get(reservation_id)

    def reservation_cancel(self, reservation_id, identity=None):
        """
        Cancel a reservation

        you can only cancel your own reservation
        Once a reservation is cancelled, it is marked as to be deleted in BCDB
        the 0-OS node then detects it an will decomission the workloads from the reservation

        :param reservation_id: reservation id
        :type reservation_id: int
        :param identity: identity to use
        :type identity: Jumpscale.tools.threebot.ThreebotMe.ThreebotMe
        :return: true if the reservation has been cancelled successfully
        :rtype: bool
        """
        me = identity if identity else j.tools.threebot.me.default

        reservation = self.reservation_get(reservation_id)
        payload = j.data.nacl.payload_build(reservation.id, reservation.json.encode())
        signature = me.nacl.sign_hex(payload)

        return self._explorer.reservations.sign_delete(reservation_id=reservation_id, tid=me.tid, signature=signature)

    def reservation_list(self, tid=None):
        tid = tid if tid else j.tools.threebot.me.default.tid
        result = self._explorer.reservations.list()
        return list(filter(lambda r: r.customer_tid == tid, result))

    def reservation_store(self, reservation, path):
        """
        write the reservation on disk.
        use reservation_load() to load it back

        :param reservation: reservation object
        :type reservation: tfgrid.workloads.reservation.1
        :param path: destination file
        :type path: str
        """
        j.data.serializers.json.dump(path, reservation._ddict)

    def reservation_load(self, path):
        """
        load a reservation stored on disk by reservation_store

        :param path: source file
        :type path: str
        :return: reservation object
        :rtype: tfgrid.workloads.reservation.1
        """
        r = j.data.serializers.json.load(path)
        reservation_model = j.data.schema.get_from_url("tfgrid.workloads.reservation.1")
        return reservation_model.new(datadict=r)

    def reservation_live(self, expired=False, cancelled=False, identity=None):
        me = identity if identity else j.tools.threebot.me.default
        rs = self._explorer.reservations.list()

        now = j.data.time.epoch

        for r in rs:
            if r.customer_tid != me.tid:
                continue

            if not expired and r.data_reservation.expiration_reservation < now:
                continue

            if not cancelled and str(r.next_action) == "DELETE":
                continue

            print(f"reservation {r.id}")

            wid_res = {result.workload_id: result for result in r.results}

            for c in r.data_reservation.containers:
                result = wid_res.get(c.workload_id)
                if not result:
                    print("container: no result")
                    continue

                data = j.data.serializers.json.loads(result.data)
                print(f"container ip4:{data['ipv4']} ip6{data['ipv6']}")

            for zdb in r.data_reservation.zdbs:
                result = wid_res.get(zdb.workload_id)
                if not result:
                    print("zdb: no result")
                    continue

                data = j.data.serializers.json.loads(result.data)
                print(f"zdb namespace:{namespace} ip:{ip} port:{port}")

            for network in r.data_reservation.networks:
                result = wid_res.get(network.workload_id)
                if not result:
                    print(f"network name:{network.name}: no result")
                    continue

                print(f"network name:{network.name} iprage:{network.iprange}")

    def reservation_failed(self, reservation):
        """
        checks if reservation failed.
        :param reservation: reservation object
        :type reservation: tfgrid.workloads.reservation.1
        :return: true if the reservation has any of its results in state ERROR.
        :rtype: bool
        """
        return any(map(lambda x: x == "ERROR", [x.state for x in reservation.results]))

    def reservation_ok(self, reservation):
        """
        checks if reservation succeeded.
        :param reservation: reservation object
        :type reservation: tfgrid.workloads.reservation.1
        :return: true if the reservation has all of its results in state OK.
        :rtype: bool
        """

        return all(map(lambda x: x == "OK", [x.state for x in reservation.results]))
