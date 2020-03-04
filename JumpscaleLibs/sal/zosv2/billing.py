from .resource import ResourceParser


class Billing:
    def __init__(self, explorer):
        self._explorer = explorer

    def reservation_resources(self, reservation):
        """
        compute how much resource units is reserved in the reservation

        :param reservation: reservation object
        :type reservation: tfgrid.workloads.reservation.1
        :return: list of ResourceUnitsNode object
        :rtype: list
        """
        rp = ResourceParser(self._explorer, reservation)
        return rp.calculate_used_resources()

    def reservation_resources_cost(self, reservation):
        """
        compute how much resource units is reserved in the reservation

        :param reservation: reservation object
        :type reservation: tfgrid.workloads.reservation.1
        :return: list of ResourceUnitsNode object with costs filled in
        :rtype: list
        """
        rp = ResourceParser(self._explorer, reservation)
        return rp.calculate_used_resources_cost()

    def payout_farmers(self, tfchain_wallet, resource_units_per_node, reservation):
        """
        payout farmer based on the resources per node used

        :param tfchain_wallet: tfchain wallet
        :type tfchain_wallet: a wallet of j.clients.tfchain
        :param resource_units_per_node: list of resource units per node retrieved from reservation_resources_cost
        :type resource_units_per_node: list of ResourceUnitsNode
        :param reservation: reservation object
        :type int
        :return: list of transactions
        :rtype: list
        """
        rp = ResourceParser(self._explorer, reservation)
        return rp.payout_farmers(tfchain_wallet, resource_units_per_node, reservation.id)

    def verify_payments(self, tfchain_wallet, reservation):
        """
        verify that a reservation with a given ID has been paid for, for all farms belonging to the current user 3bot

        :param tfchain_wallet: tfchain wallet
        :type tfchain_wallet: a wallet of j.clients.tfchain
        :param reservation_id: the id of the reservation to verify
        :type reservation_id: int
        :return: if the reservation has been fully funded for the farms owned by the current user 3bot
        :rtype: bool
        """
        rp = ResourceParser(self._explorer, reservation)
        return rp.validate_reservation_payment(tfchain_wallet, reservation.id)
