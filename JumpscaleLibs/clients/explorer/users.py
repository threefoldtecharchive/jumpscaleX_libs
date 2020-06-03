from nacl.encoding import Base64Encoder

from Jumpscale import j

from .auth import HTTPSignatureAuth
from .pagination import get_all, get_page


class Users:
    def __init__(self, session, url):
        self._session = session
        self._base_url = url
        self._model = j.data.schema.get_from_url("tfgrid.phonebook.user.1")

    def list(self, name=None, email=None, page=None, identity=None):
        me = identity if identity else j.me
        secret = me.encryptor.signing_key.encode(Base64Encoder)

        auth = HTTPSignatureAuth(key_id=str(me.tid), secret=secret, headers=["(created)", "date", "threebot-id"])
        headers = {"threebot-id": str(me.tid)}

        url = self._base_url + "/users"

        query = {}
        if name is not None:
            query["name"] = name
        if email is not None:
            query["email"] = email

        if page:
            users, _ = get_page(self._session, page, self._model, url, query=query, auth=auth, headers=headers)
        else:
            users = list(self.iter(name=name, email=email, identity=identity))

        return users

    def iter(self, name=None, email=None, identity=None):
        me = identity if identity else j.me
        secret = me.encryptor.signing_key.encode(Base64Encoder)

        auth = HTTPSignatureAuth(key_id=str(me.tid), secret=secret, headers=["(created)", "date", "threebot-id"])
        headers = {"threebot-id": str(me.tid)}

        url = self._base_url + "/users"
        query = {}
        if name is not None:
            query["name"] = name
        if email is not None:
            query["email"] = email
        yield from get_all(self._session, self._model, url, query=query, auth=auth, headers=headers)

    def new(self):
        return self._model.new()

    def register(self, user):
        resp = self._session.post(self._base_url + "/users", json=user._ddict)
        return resp.json()["id"]

    def validate(self, tid, payload, signature):
        url = self._base_url + f"/users/{tid}/validate"
        data = {
            "payload": payload,
            "signature": signature,
        }

        resp = self._session.post(url, json=data)
        return resp.json()["is_valid"]

    def update(self, user, identity=None):
        me = identity if identity else j.me
        datatosign = ""
        datatosign += f"{user.id}{user.name}{user.email}"
        if user.host:
            datatosign += user.host
        datatosign += f"{user.description}{user.pubkey}"
        signature = me.encryptor.sign_hex(datatosign.encode("utf8"))
        data = user._ddict.copy()
        data["sender_signature_hex"] = signature.decode("utf8")
        self._session.put(self._base_url + f"/users/{user.id}", json=data)

    def get(self, tid=None, name=None, email=None, identity=None):
        me = identity if identity else j.me
        secret = me.encryptor.signing_key.encode(Base64Encoder)

        auth = HTTPSignatureAuth(key_id=str(me.tid), secret=secret, headers=["(created)", "date", "threebot-id"])
        headers = {"threebot-id": str(me.tid)}

        if tid is not None:
            resp = self._session.get(self._base_url + f"/users/{tid}", auth=auth, headers=headers)
            return self._model.new(datadict=resp.json())

        results = self.list(name=name, email=email, identity=identity)
        if results:
            return results[0]
        raise j.exceptions.NotFound("user not found")
