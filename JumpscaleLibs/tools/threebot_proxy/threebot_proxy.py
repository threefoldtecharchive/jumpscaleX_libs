import nacl.encoding
import nacl.exceptions
import requests
import json

from bottle import redirect, request, abort
from functools import wraps
from urllib.parse import urlencode

from Jumpscale import j

try:
    from beaker.middleware import SessionMiddleware
except (ModuleNotFoundError, ImportError):
    j.builders.runtimes.python3.pip_package_install("beaker")
    from beaker.middleware import SessionMiddleware


_session_opts = {"session.type": "file", "session.data_dir": "./data", "session.auto": True}


class ThreebotProxy(j.baseclasses.object):
    def __init__(self, app):
        self.app = SessionMiddleware(app, _session_opts)
        self.nacl = j.data.nacl.default

    @property
    def session(self):
        return request.environ.get("beaker.session")

    @property
    def next_url(self):
        return self.session.get("next_url", "/")

    def login(self, app_id, callback_url):
        state = j.data.idgenerator.generateXCharID(20)
        self.session["state"] = state
        redirect_url = "https://login.threefold.me"

        params = {
            "state": state,
            "appid": app_id,
            "scope": j.data.serializers.json.dumps({"user": True, "email": True}),
            "redirecturl": callback_url,
            "publickey": self.nacl.public_key.encode(encoder=nacl.encoding.Base64Encoder),
        }
        params = urlencode(params)
        return redirect(f"{redirect_url}?{params}", code=302)

    def callback(self):
        signed_hash = request.params.get("signedhash")
        username = request.params.get("username")
        data = request.params.get("data")

        if signed_hash is None or username is None or data is None:
            return abort(400, "Request must contain signedhash, username, and data.")
        data = j.data.serializers.json.loads(data)

        res = requests.get(f"https://login.threefold.me/api/users/{username}", {"Content-Type": "application/json"})
        if res.status_code != 200:
            return abort(400, "Error getting user pub key")

        pub_key = res.json()["publicKey"]
        user_pub = j.data.nacl.verifykey_obj_get(j.data.serializers.base64.decode(pub_key))
        nonce = j.data.serializers.base64.decode(data["nonce"])
        ciphertext = j.data.serializers.base64.decode(data["ciphertext"])
        state = user_pub.verify(j.data.serializers.base64.decode(signed_hash)).decode()

        if state != self.session["state"]:
            return abort(400, "Invalid state. not matching one in user session")

        try:
            decrypted = self.nacl.decryptAsymmetric(user_pub.to_curve25519_public_key(), ciphertext, nonce)
        except nacl.exceptions.CryptoError:
            return abort(400, "Error decrypting data")

        try:
            result = j.data.serializers.json.loads(decrypted)
        except json.JSONDecodeError:
            return abort(400, "3bot login returned faulty data")

        if "email" not in result:
            return abort(400, "Email is not present in data")

        if not result["email"]["verified"]:
            return abort(400, "Email not verified")

        self.session["email"] = result["email"]["email"]
        self.session["authorized"] = True
        return redirect(self.next_url)

    def login_required(self, func):
        @wraps(func)
        def decorator(*args, **kwargs):
            if not self.session.get("authorized", False):
                self.session["next_url"] = request.path
                return redirect(self.login_url)
            return func(*args, **kwargs)

        return decorator


class ThreebotProxyFactory(j.baseclasses.factory):
    __jslocation__ = "j.tools.threebotlogin_proxy"

    def get(self, app):
        return ThreebotProxy(app)
