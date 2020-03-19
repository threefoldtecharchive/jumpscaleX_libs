from Jumpscale import j


class Users:
    def __init__(self, session, url):
        self._session = session
        self._base_url = url
        j.data.schema.add_from_path(
            "/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/phonebook/models"
        )
        self._user_model = j.data.schema.get_from_url("tfgrid.phonebook.user.1")

    def list(self, name=None, email=None):
        query = {}
        if name is not None:
            query["name"] = name
        if email is not None:
            query["email"] = email
        resp = self._session.get(self._base_url + "/users", params=query)
        resp.raise_for_status()
        users = []
        for user_data in resp.json():
            user = self._user_model.new(datadict=user_data)
            users.append(user)
        return users

    def new(self):
        return self._user_model.new()

    def register(self, user):
        resp = self._session.post(self._base_url + "/users", json=user._ddict)
        resp.raise_for_status()
        return resp.json()

    def validate(self, tid, payload, signature):
        url = self._base_url + f"/users/{tid}/validate"
        data = {
            "payload": payload,
            "signature": signature,
        }

        resp = self._session.post(url, json=data)
        resp.raise_for_status()
        return resp.json()["is_valid"]

    def update(self, user):
        resp = self._session.put(self._base_url + "/users", json=user._ddict)
        resp.raise_for_status()

    def get(self, tid=None, name=None, email=None):
        if tid != None:
            resp = self._session.get(self._base_url + f"/users/{tid}")
            resp.raise_for_status()
            return self._user_model.new(datadict=resp.json())

        results = self.list(name=name, email=email)
        if results:
            return results[0]
        raise j.exceptions.NotFound("user not found")

