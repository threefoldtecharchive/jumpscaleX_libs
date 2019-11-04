from bottle import redirect, request, abort
from urllib.parse import urlencode
from Jumpscale import j
import binascii
import nacl.encoding
import requests
from nacl.public import Box

from functools import wraps

try:
    from beaker.middleware import SessionMiddleware
except (ModuleNotFoundError, ImportError):
    j.builders.runtimes.python3.pip_package_install("beaker")
    from beaker.middleware import SessionMiddleware


session_opts = {"session.type": "file", "session.data_dir": "./data", "session.auto": True}


class ThreebotProxy(j.baseclasses.object):
    def __init__(self, app):
        self.app = SessionMiddleware(app, session_opts)
        self.nacl = j.data.nacl.default

    @property
    def session(self):
        return request.environ.get("beaker.session")

    @property
    def next_url(self):
        return self.session.get("next_url", "/")

    def login(self, callback_url):
        state = j.data.idgenerator.generateXCharID(20)
        self.session["state"] = state
        redirect_url = "https://login.threefold.me"

        params = {
            "state": state,
            "appid": request.urlparts.netloc,
            "scope": "{'user': true, 'email': true}",
            "redirecturl": callback_url,
            "publickey": self.nacl.signing_key.verify_key.to_curve25519_public_key().encode(
                encoder=nacl.encoding.Base64Encoder
            ),
        }
        params = urlencode(params)
        return redirect(f"{redirect_url}?{params}", code=302)

    def callback(self):
        import ipdb

        ipdb.set_trace()
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

        box = Box(self.nacl.signing_key.to_curve25519_private_key(), user_pub.to_curve25519_public_key())

        try:
            decrypted = box.decrypt(ciphertext, nonce)
            result = json.loads(decrypted)
            email = result["email"]["email"]
            emailVerified = result["email"]["verified"]
            if not emailVerified:
                return abort(400, "Email not verified")

            bot_app.session["email"] = email
            self.session["authorized"] = True
            return redirect(bot_app.next_url)

        except:
            return abort(400, "Error decrypting data")


class ThreebotProxyFactory(j.baseclasses.factory):
    __jslocation__ = "j.tools.threebotlogin_proxy"

    def get(self, app):
        return ThreebotProxy(app)
