"""
Minio Client
"""

from Jumpscale import j
import requests

JSConfigClient = j.baseclasses.object_config


class MinioClient(JSConfigClient):
    """
    Minio client object
    """

    _SCHEMATEXT = """
        @url = jumpscale.minio.client
        url** = "" (S)
        """

    def get_jobs(self):
        resp = requests.post(self.url + '/jobs')
        resp.raise_for_status()
        return resp.json()