from Jumpscale import j


class Nodes:
    def __init__(self, session, url):
        self._session = session
        self._base_url = url
        j.data.schema.add_from_path(
            "/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/directory/models"
        )
        self._node_model = j.data.schema.get_from_url("tfgrid.directory.node.2")

    def list(self, farm_id=None, proofs=False):
        query = {}
        if farm_id is not None:
            query["farm"] = farm_id
        if proofs:
            query["proofs"] = "true"
        resp = self._session.get(self._base_url + "/nodes", params=query)
        resp.raise_for_status()
        nodes = []
        for node_data in resp.json():
            node = self._node_model.new(datadict=node_data)
            nodes.append(node)
        return nodes

    def get(self, node_id, proofs=False):
        params = {}
        if proofs:
            params["proofs"] = "true"
        resp = self._session.get(self._base_url + f"/nodes/{node_id}", params=params)
        resp.raise_for_status()
        return self._node_model.new(datadict=resp.json())