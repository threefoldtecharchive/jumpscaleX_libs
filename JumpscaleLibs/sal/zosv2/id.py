_NULL_INT = 2147483647


def _next_workload_id(reservation):
    """
    returns the next workload id available in the reservation
    """
    max = 0
    for _type in ["zdbs", "volumes", "containers", "networks", "kubernetes"]:
        for workload in getattr(reservation.data_reservation, _type):
            if workload.workload_id < _NULL_INT and max < workload.workload_id:
                max = workload.workload_id
    return max + 1
