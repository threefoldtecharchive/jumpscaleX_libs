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

    def payout_farmers(self, client, reservation):
        """
        payout farmer based on the resources per node used

        :param client: tfchain wallet or stellar client
        :type client: a wallet of j.clients.tfchain or a client of j.client.stellar
        :param reservation: reservation object
        :type reservation: tfgrid.workloads.reservation.1
        :return: list of transactions
        :rtype: list
        """
        rp = ResourceParser(self._explorer, reservation)
        costs = rp.calculate_used_resources_cost()
        return rp.payout_farmers(client, costs, reservation.id)

    def verify_payments(self, client, reservation):
        """
        verify that a reservation with a given ID has been paid for, for all farms belonging to the current user 3bot

        :param client: tfchain wallet or stellar client
        :type client: a wallet of j.clients.tfchain or a client of j.client.stellar
        :param reservation: reservation object
        :type reservation: tfgrid.workloads.reservation.1
        :return: if the reservation has been fully funded for the farms owned by the current user 3bot
        :rtype: bool
        """
        rp = ResourceParser(self._explorer, reservation)
        return rp.validate_reservation_payment(client, reservation.id)
