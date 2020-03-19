from Jumpscale import j


class Nodes:
    def __init__(self, session, url):
        self._session = session
        self._base_url = url
        j.data.schema.add_from_path(
            "/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/directory/models"
        )
        self._model = j.data.schema.get_from_url("tfgrid.directory.node.2")

    def list(self, farm_id=None, country=None, city=None, cru=None, sru=None, mru=None, hru=None, proofs=False):
        query = {}
        if proofs:
            query["proofs"] = "true"
        args = {
            "farm_id": farm_id,
            "city": city,
            "cru": cru,
            "sru": sru,
            "mru": mru,
            "hru": hru,
        }
        for k, v in args.items():
            if v is not None:
                query[k] = v

        resp = self._session.get(self._base_url + "/nodes", params=query)
        nodes = []
        for node_data in resp.json():
            node = self._model.new(datadict=node_data)
            nodes.append(node)
        return nodes

    def get(self, node_id, proofs=False):
        params = {}
        if proofs:
            params["proofs"] = "true"
        resp = self._session.get(self._base_url + f"/nodes/{node_id}", params=params)
        return self._model.new(datadict=resp.json())
