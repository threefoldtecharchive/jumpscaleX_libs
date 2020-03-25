from requests import HTTPError


def raise_for_status(resp, *args, **kwargs):
    http_error_msg = ""
    if 400 <= resp.status_code < 500:
        reason = resp.json()["error"]
        http_error_msg = f"{resp.status_code} Client Error: {reason} for url: {resp.url}"

    elif 500 <= resp.status_code < 600:
        reason = resp.json()["error"]
        http_error_msg = f"{resp.status_code} Server Error: {reason} for url: {resp.url}"

    if http_error_msg:
        raise HTTPError(http_error_msg, response=resp)
