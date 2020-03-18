from Jumpscale import j


class Directory:
    def __init__(self, session, url):
        self._session = session
        self._base_url = url
        j.data.schema.add_from_path(
            "/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/directory/models"
        )
        self.node_model = j.data.schema.get_from_url("tfgrid.directory.node.2")
        self.farm_model = j.data.schema.get_from_url("tfgrid.directory.farm.1")

