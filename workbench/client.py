import httpx
from . import store


def companion(path, body=None, timeout=150):
    with httpx.Client(timeout=timeout) as client:
        response = client.request("POST" if body is not None else "GET", "http://127.0.0.1:8766" + path, headers={"Authorization": "Bearer " + store.current_token()}, json=body)
        if response.is_error:
            raise ValueError(response.json().get("detail", "Companion rejected action"))
        return response.json()
