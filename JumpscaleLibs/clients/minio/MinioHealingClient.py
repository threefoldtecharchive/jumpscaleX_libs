"""
Minio Healing Client
"""

from Jumpscale import j
import requests
from urllib.parse import urljoin

JSConfigClient = j.baseclasses.object_config


class MinioHealingClient(JSConfigClient):
    """
    Minio healing client object
    """

    _SCHEMATEXT = """
        @url = jumpscale.minio.client
        name** = "" (S)
        url** = "" (S)
        """

    def get_jobs(self):
        resp = requests.get(f"{self.url}/jobs")
        resp.raise_for_status()
        jobs = resp.json()

        minio_jobs = []
        for job_id, job in jobs.items():
            minio_jobs.append(MinioJob(self.url, job_id=job_id, job=job))
        return minio_jobs

    def heal(self, report=None, dry_run=False, bucket=None, object_path=None):
        getVars = {}

        if report:
            getVars["bg"] = 1
        if dry_run:
            getVars["dry-run"] = 1

        url = urljoin(self.url, "repair/")
        if bucket is not None:
            if object_path is not None:
                url = urljoin(url, f"{bucket}/{object_path}")
            else:
                url = urljoin(url, f"{bucket}")

        if report is None:
            resp = requests.post(url, params=getVars)
            resp.raise_for_status()
            return resp.text
        else:
            resp = requests.post(url, params=getVars)
            resp.raise_for_status()
            return read_response_chuncked(resp, report)

def read_response_chuncked(response, file_path):
    if file_path == "":
        return Exception("you must provide a file path")

    with open(file_path, "w+") as f:
        block_size = 512
        response.encoding = "utf-8"
        for chunk in response.iter_content(chunk_size=block_size, decode_unicode=True):
            f.write(chunk)

class MinioJob(object):
    def __init__(self, url, job_id, job) -> None:
        self.url = url
        self.__job_id = job_id
        self.__job = job

    @property
    def running(self):
        return self.__job["running"]

    @property
    def job_type(self):
        return self.__job["type"]

    @property
    def location(self):
        return self.__job["location"]

    @property
    def blobs(self):
        return self.__job.get("blobs")

    @property
    def objects(self):
        return self.__job.get("objects")

    def delete(self) -> None:
        """
        Delete this job
        """
        resp = requests.delete(f"{self.url}/jobs/{self.__job_id}")
        resp.raise_for_status()
        return resp.ok

    def __str__(self):
        return f"""
Minio healing job: {self.__job_id}
Location: {self.location}
Job Type: {self.job_type}
Running: {self.running}
Blobs: {self.blobs}
Objects: {self.objects}
"""

    def __repr__(self):
        return str(self)