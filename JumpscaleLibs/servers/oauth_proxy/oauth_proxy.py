from bottle import redirect, request, abort
from urllib.parse import urlencode
from Jumpscale import j

from functools import wraps

try:
    from beaker.middleware import SessionMiddleware
except (ModuleNotFoundError, ImportError):
    j.builders.runtimes.python3.pip_package_install("beaker")
    from beaker.middleware import SessionMiddleware


session_opts = {"session.type": "file", "session.data_dir": "./data", "session.auto": True}


class OauthProxy(j.baseclasses.object):
    def __init__(self, app, oauth2_proxy_url=None, login_endpoint=None, redirect_endpoint=None):
        self.app = SessionMiddleware(app, session_opts)
        self.oauth2_proxy_url = oauth2_proxy_url
        self.redirect_endpoint = redirect_endpoint
        self.login_endpoint = login_endpoint
        self.__current_provider = None

    @property
    def session(self):
        return request.environ.get("beaker.session")

    @property
    def login_url(self):
        return "{X-Forwarded-Proto}://{Host}{login_endpoint}".format(
            login_endpoint=self.login_endpoint, **request.headers
        )

    @property
    def redirect_url(self):
        return "{X-Forwarded-Proto}://{Host}{redirect_endpoint}".format(
            redirect_endpoint=self.redirect_endpoint, **request.headers
        )

    @property
    def next_url(self):
        return self.session.get("next_url", "/")

    @property
    def current_provider(self):
        if self.__current_provider is None:
            provider_name = self.session.get("provider")
            if provider_name:
                return j.clients.oauth2_provider.get(name=provider_name)
        else:
            return self.__current_provider

    def _validate_uid(self, uid):
        print(uid, self.session.get("uid"))
        if uid != self.session.get("uid"):
            return abort(400, "Invalid user uid")

    def get_access_token(self, code, state):
        self._validate_uid(state)
        return self.current_provider.get_access_token(code, state)

    def login(self, provider):
        uid = j.data.idgenerator.generateGUID()
        self.session["uid"] = uid
        self.session["provider"] = provider
        params = {"uid": uid, "redirect_url": self.redirect_url}
        rurl = f"{self.oauth2_proxy_url}/{provider}?{urlencode(params)}"
        return redirect(rurl)

    def authorize(self, provider, uid, redirect_url):
        self.session["uid"] = uid
        self.session["provider"] = provider
        self.session["redirect_url"] = redirect_url
        rurl = self.current_provider.get_authorization_url(uid)
        return redirect(rurl)

    def authorize_user(self):
        self.session["authotized"] = True

    def unauthorize_user(self):
        self.session["authotized"] = False

    def oauth2_callback(self):
        code = request.query.get("code")
        state = request.query.get("state")
        redirect_url = self.session.get("redirect_url")
        access_token = self.get_access_token(code, state)
        userinfo = self.current_provider.get_user_info(access_token)
        userinfo["uid"] = state
        rurl = f"{redirect_url}?{urlencode(userinfo)}"
        return redirect(rurl)

    def callback(self):
        data = dict(request.query)
        uid = data.pop("uid", None)
        self._validate_uid(uid)
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
    __jslocation__ = "j.servers.oauth_proxy"

    def get(self, app, oauth2_proxy_url=None, login_endpoint=None, redirect_endpoint=None):
        return OauthProxy(app, oauth2_proxy_url, login_endpoint, redirect_endpoint)
