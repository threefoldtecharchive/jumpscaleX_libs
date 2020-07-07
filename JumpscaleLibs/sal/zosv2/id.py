_NULL_INT = 2147483647


def _next_workload_id(reservation):
    """
    returns the next workload id available in the reservation
    """
    max = 0
    for _type in [
        "zdbs",
        "volumes",
        "containers",
        "networks",
        "kubernetes",
        "proxies",
        "reverse_proxies",
        "subdomains",
        "domain_delegates",
    ]:
        for workload in getattr(reservation.data_reservation, _type):
            if workload.info.workload_id < _NULL_INT and max < workload.info.workload_id:
                max = workload.workload_id
    return max + 1
