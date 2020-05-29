"""
Minio Healing Client
"""

from Jumpscale import j
import requests

JSConfigClient = j.baseclasses.object_config


class MinioClient(JSConfigClient):
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
            minio_job = MinioJob(
                self.url, job_id, job["location"], job["type"], job["running"]
            )
            minio_jobs.append(minio_job)
        return minio_jobs

    def heal(self, background=False, file_path=""):
        url = f"{self.url}/repair"
        if background:
            url += "?bg=1"
            resp = requests.post(url)
            resp.raise_for_status()
            return resp.text
        else:
            resp = requests.post(url)
            resp.raise_for_status()
            return self._read_response_chuncked(resp, file_path)
    
    def repair_bucket(self, bucket_name, background=False, file_path=""):
        url = f"{self.url}/repair/{bucket_name}"
        if background:
            url += "?bg=1"
            resp = requests.post(url)
            resp.raise_for_status()
            return resp.text
        else:
            resp = requests.post(url)
            resp.raise_for_status()
            return self._read_response_chuncked(resp, file_path)

    def repair_bucket_object(self, object_path, background=False, file_path=""):
        url = f"{self.url}/repair/{object_path}"
        if background:
            url += "?bg=1"
            resp = requests.post(url)
            resp.raise_for_status()
            return resp.text
        else:
            resp = requests.post(url)
            resp.raise_for_status()
            return self._read_response_chuncked(resp, file_path)

    def _read_response_chuncked(self, response, file_path):
        if file_path == "":
            return Exception("you must provide a file path")
        
        with open(file_path, 'w+') as f:
            count = 1
            block_size = 512
            try:
                total_size = int(response.headers.get('content-length'))
            except TypeError:
                total_size = 10000000

            response.encoding = 'utf-8'
            for chunk in response.iter_content(chunk_size=block_size, decode_unicode=True):
                if chunk:
                    f.write(chunk)                                                                                                                                                                                                                                   
                    f.flush()

class MinioJob(object):
    def __init__(self, url, job_id: str, location: str, job_type: str, running: bool) -> None:
        self.url = url
        self.job_id = job_id
        self.location = location
        self.job_type = job_type
        self.running = running

    def delete(self) -> None:
        """
        Delete this job
        """
        resp = requests.delete(f"{self.url}/jobs/{self.job_id}")
        resp.raise_for_status()
        return resp.ok

    def __str__(self):
        return f"""
Minio healing job: {self.job_id}
Location: {self.location}
Job Type: {self.job_type}
Running: {self.running}
"""

    def __repr__(self):
        return str(self)