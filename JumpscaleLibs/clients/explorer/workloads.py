from Jumpscale import j


class Workloads:
    def __init__(self, session, url):
        self._session = session
        self._base_url = url
        j.data.schema.add_from_path(
            "/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/workloads/models"
        )
        self._model = j.data.schema.get_from_url("tfgrid.workloads.reservation.1")

