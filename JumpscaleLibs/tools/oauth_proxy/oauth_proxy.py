from bottle import redirect, request, abort
from urllib.parse import urlencode
from Jumpscale import j
import binascii

from functools import wraps

try:
    from beaker.middleware import SessionMiddleware
except (ModuleNotFoundError, ImportError):
    j.builders.runtimes.python3.pip_package_install("beaker")
    from beaker.middleware import SessionMiddleware


session_opts = {"session.type": "file", "session.data_dir": "./data", "session.auto": True}


class OauthProxy(j.baseclasses.object):
    def __init__(self, app, client, login_url=None):
        self.app = SessionMiddleware(app, session_opts)
        self.client = client
        self.login_url = login_url
        self.nacl = j.data.nacl.default
        self.verify_key = binascii.unhexlify(client.verify_key)

    @property
    def session(self):
        return request.environ.get("beaker.session")

    @property
    def next_url(self):
        return self.session.get("next_url", "/")

    @property
    def current_provider(self):
        provider = self.session.get("provider")
        if provider and provider in self.client.providers_list():
            return j.clients.oauth_provider.get(provider)
        else:
            return abort(400, f"Provider {provider} is not supported")

    def login(self, provider, redirect_url):
        state = j.data.idgenerator.generateGUID()
        self.session["state"] = state
        self.session["provider"] = provider

        # redirect user to oauth proxy
        params = dict(provider=provider, state=state, redirect_url=redirect_url)
        rurl = f"{self.client.url}/authorize?{urlencode(params)}"
        return redirect(rurl)

    def authorize(self):
        state = request.query.get("state")
        provider = request.query.get("provider")
        redirect_url = request.query.get("redirect_url")

        # save state, provider and redirect url in session
        self.session["state"] = state
        self.session["provider"] = provider
        self.session["redirect_url"] = redirect_url

        # redirect user to provider url
        rurl = self.current_provider.get_authorization_url(state=state)
        return redirect(rurl)

    def oauth_callback(self):
        code = request.query.get("code")
        state = request.query.get("state")

        # validate the state
        if state != self.session.get("state"):
            return abort(400, "Invalid state")

        # get user info
        access_token = self.current_provider.get_access_token(code, state)
        userinfo = self.current_provider.get_user_info(access_token)

        # generate signature
        payload = urlencode(dict(state=state, **userinfo)).encode()
        signature = self.nacl.sign_hex(payload).decode()

        # redirect user to the redirect url
        redirect_url = self.session.get("redirect_url")
        rurl = f"{redirect_url}?{urlencode(userinfo)}&signature={signature}"
        return redirect(rurl)

    def callback(self):
        data = dict(request.query)
        state = self.session.get("state")
        signature_hex = data.pop("signature")
        signature = binascii.unhexlify(signature_hex.encode())
        payload = dict(state=state, **data)
        required_fields = self.current_provider.user_info_fields

        if not self.nacl.verify(urlencode(payload).encode(), signature, verify_key=self.verify_key) or not set(
            data.keys()
        ).issuperset(required_fields):
            return abort(401, "Unauthorized")

        self.session["authotized"] = True
        return data

    def login_required(self, func):
        @wraps(func)
        def decorator(*args, **kwargs):
            if not self.session.get("authotized", False):
                self.session["next_url"] = request.path
                return redirect(self.login_url)
            return func(*args, **kwargs)

        return decorator


class OauthProxyFactory(j.baseclasses.factory):
    __jslocation__ = "j.tools.oauth_proxy"

    def get(self, app, client, login_url=None):
        return OauthProxy(app, client, login_url)
