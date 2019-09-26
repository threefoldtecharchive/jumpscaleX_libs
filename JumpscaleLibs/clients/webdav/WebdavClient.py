from Jumpscale import j

try:
    import webdav.client as wc
except:
    j.builders.system.package.mdupdate()
    j.builders.system.package.install("libxml2-dev libxslt-dev python3-dev libcurl4-openssl-dev python-pycurl")
    j.builders.runtimes.python3.pip_package_install("webdavclient")
    import webdav.client as wc

JSConfigClient = j.baseclasses.object_config


class WebdavClient(JSConfigClient):
    _SCHEMATEXT = """
    @url = jumpscale.webdav.client
    name** = "" (S)
    url = "" (S)
    username = "" (S)
    password = "" (S)
    """

    def _init(self, **kwargs):
        """ connect to webdav server
        """

        options = {
            "webdav_hostname": f"{self.url}",
            "webdav_login": f"{self.username}",
            "webdav_password": f"{self.password}",
        }
        self.client = wc.Client(options)

    def list(self, path):
        return self.client.list(path)

    def exists(self, path):
        return self.client.check(path)

    def delete(self, path):
        return self.client.clean(path)

    def create_dir(self, path):
        self.client.mkdir(path)
        return True

    def get_info(self, path):
        return self.client.info(path)

    def copy(self, from_path, to_path):
        self.client.copy(from_path, to_path)
        return True

    def move(self, old_path, new_path):
        self.client.move(old_path, new_path)
        return True

    def download(self, remote_path, local_path):
        self.client.download_sync(remote_path, local_path)
        return True

    def upload(self, local_path, remote_path):
        self.client.upload_sync(remote_path, local_path)
        return True

    def sync_to_local(self, remote_dir, local_dir):
        self.client.pull(remote_dir, local_dir)
        return True
