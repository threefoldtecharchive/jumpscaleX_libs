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
    def __init__(self, app, login_url):
        self.app = SessionMiddleware(app, _session_opts)
        self.nacl = j.me.encryptor
        self.login_url = login_url

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

        # @TODO: #public_key.to_curve25519_public_key()?
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

        data = request.query.get("signedAttempt")

        if not data:
            return abort(400, "signedAttempt parameter is missing")

        data = json.loads(data)

        if "signedAttempt" not in data:
            return abort(400, "signedAttempt value is missing")

        username = data["doubleName"]

        if not username:
            return abort(400, "DoubleName is missing")

        res = requests.get(f"https://login.threefold.me/api/users/{username}", {"Content-Type": "application/json"})
        if res.status_code != 200:
            return abort(400, "Error getting user pub key")
        pub_key = res.json()["publicKey"]
        user_pub_key = j.me.encryptor._verify_key_get(j.data.serializers.base64.decode(pub_key))

        # verify data
        signedData = data["signedAttempt"]

        verifiedData = user_pub_key.verify(j.data.serializers.base64.decode(signedData)).decode()

        data = json.loads(verifiedData)

        if "doubleName" not in data:
            return abort(400, "Decrypted data does not contain (doubleName)")

        if "signedState" not in data:
            return abort(400, "Decrypted data does not contain (state)")

        if data["doubleName"] != username:
            return abort(400, "username mismatch!")

        # verify state
        state = data["signedState"]
        if state != self.session["state"]:
            return abort(400, "Invalid state. not matching one in user session")

        nonce = j.data.serializers.base64.decode(data["data"]["nonce"])
        ciphertext = j.data.serializers.base64.decode(data["data"]["ciphertext"])

        try:
            decrypted = j.me.encryptor.decrypt(ciphertext, user_pub_key.to_curve25519_public_key(), nonce=nonce)
        except nacl.exceptions.CryptoError:
            return abort(400, "Error decrypting data")

        try:
            result = j.data.serializers.json.loads(decrypted)
        except json.JSONDecodeError:
            return abort(400, "3bot login returned faulty data")

        if "email" not in result:
            return abort(400, "Email is not present in data")

        email = result["email"]["email"]

        sei = result["email"]["sei"]
        res = requests.post(
            "https://openkyc.live/verification/verify-sei",
            headers={"Content-Type": "application/json"},
            json={"signedEmailIdentifier": sei},
        )

        if res.status_code != 200:
            return abort(400, "Email is not verified")

        self.session["username"] = username
        self.session["email"] = email
        self.session["authorized"] = True
        return redirect(self.next_url)

    def login_required(self, func):
        @wraps(func)
        def decorator(*args, **kwargs):
            if j.core.myenv.config.get("THREEBOT_CONNECT", False):
                if not self.session.get("authorized", False):
                    self.session["next_url"] = request.url
                    return redirect(self.login_url)
            return func(*args, **kwargs)

        return decorator


class ThreebotProxyFactory(j.baseclasses.factory):
    __jslocation__ = "j.me.encryptor.toolslogin_proxy"

    def get(self, app, login_url):
        return ThreebotProxy(app, login_url)
