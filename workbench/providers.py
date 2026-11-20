import httpx
from pydantic import SecretStr

from .store import CIPHER

DEFAULTS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta",
    "openrouter": "https://openrouter.ai/api/v1",
    "xai": "https://api.x.ai/v1",
    "ollama": "http://127.0.0.1:11434",
    "lmstudio": "http://127.0.0.1:1234/v1",
    "compatible": "http://127.0.0.1:8000/v1",
}


def key(connection):
    return CIPHER.decrypt(connection["secret"].encode()).decode() if connection.get("secret") else ""


def public(connection):
    return {name: value for name, value in connection.items() if name != "secret"} | {"has_key": bool(connection.get("secret"))}


class Adapter:
    def __init__(self, connection):
        self.connection = connection
        self.base = connection["url"].rstrip("/")
        self.secret = key(connection)

    def headers(self):
        return {"Authorization": f"Bearer {self.secret}"} if self.secret else {}

    def discover(self):
        return self.pages("/models", "data", "id")

    def pages(self, path, collection, identifier):
        result, params = [], {}
        with httpx.Client(timeout=20, follow_redirects=False) as client:
            for _ in range(100):
                response = client.get(self.base + path, headers=self.headers(), params=params)
                self.check(response)
                body = response.json()
                for model in body.get(collection, []):
                    result.append({"id": model[identifier].removeprefix("models/"), "source": "discovered", "tools": "tools" in model["supported_parameters"] if "supported_parameters" in model else None, "vision": "image" in model["architecture"].get("input_modalities", []) if model.get("architecture", {}).get("input_modalities") else None, "streaming": None})
                if body.get("nextPageToken"):
                    params = {"pageToken": body["nextPageToken"]}
                elif body.get("has_more") and body.get("last_id"):
                    params = {"after_id" if self.connection["type"] == "anthropic" else "after": body["last_id"]}
                else:
                    return result
        raise ValueError("Provider exceeded 100 discovery pages; narrow the endpoint.")

    @staticmethod
    def check(response):
        if response.status_code in (401, 403):
            raise ValueError("Credentials rejected or insufficient provider permission.")
        if response.is_error:
            raise ValueError(f"Provider returned HTTP {response.status_code}; check endpoint, model availability and quota.")

    def llm_config(self, model):
        return dict(model="openai/" + model, base_url=self.base, api_key=SecretStr(self.secret or "local"))


class Anthropic(Adapter):
    def headers(self):
        return {"x-api-key": self.secret, "anthropic-version": "2023-06-01"}

    def llm_config(self, model):
        return dict(model="anthropic/" + model, base_url=self.base, api_key=SecretStr(self.secret))


class Gemini(Adapter):
    def headers(self):
        return {"x-goog-api-key": self.secret}

    def discover(self):
        return self.pages("/models", "models", "name")

    def llm_config(self, model):
        return dict(model="gemini/" + model, base_url=self.base, api_key=SecretStr(self.secret))


class Ollama(Adapter):
    def discover(self):
        models = self.pages("/api/tags", "models", "name")
        with httpx.Client(timeout=20) as client:
            for model in models:
                response = client.post(self.base + "/api/show", headers=self.headers(), json={"model": model["id"]})
                if response.is_success:
                    capabilities = response.json().get("capabilities")
                    if isinstance(capabilities, list):
                        model["tools"] = "tools" in capabilities
                        model["vision"] = "vision" in capabilities
        return models

    def llm_config(self, model):
        return dict(model="openai/" + model, base_url=self.base + "/v1", api_key=SecretStr(self.secret or "local"))


ADAPTERS = {"anthropic": Anthropic, "gemini": Gemini, "ollama": Ollama}


def adapter(connection):
    return ADAPTERS.get(connection["type"], Adapter)(connection)


LOCAL_PROBES = [
    {
        "type": "ollama",
        "name": "Ollama",
        "url": "http://127.0.0.1:11434",
        "path": "/api/tags",
        "collection": "models",
        "id_key": "name",
    },
    {
        "type": "lmstudio",
        "name": "LM Studio",
        "url": "http://127.0.0.1:1234/v1",
        "path": "/models",
        "collection": "data",
        "id_key": "id",
    },
    {
        "type": "compatible",
        "name": "Local Compatible (Port 8000)",
        "url": "http://127.0.0.1:8000/v1",
        "path": "/models",
        "collection": "data",
        "id_key": "id",
    },
    {
        "type": "compatible",
        "name": "Local Compatible (Port 18768)",
        "url": "http://127.0.0.1:18768/v1",
        "path": "/models",
        "collection": "data",
        "id_key": "id",
    },
]


def probe_local_engine(probe, timeout=1.0):
    import time
    started = time.perf_counter()
    url = probe["url"].rstrip("/") + probe["path"]
    try:
        with httpx.Client(timeout=timeout, follow_redirects=False) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                body = resp.json()
                items = body.get(probe["collection"], [])
                models = [
                    m[probe["id_key"]]
                    for m in items
                    if isinstance(m, dict) and probe["id_key"] in m
                ][:15]
                latency_ms = round((time.perf_counter() - started) * 1000)
                return {
                    "type": probe["type"],
                    "name": probe["name"],
                    "url": probe["url"],
                    "detected": True,
                    "latency_ms": latency_ms,
                    "model_count": len(items),
                    "models": models,
                }
    except Exception:
        pass
    return None


def detect_local_engines(timeout=1.0):
    import concurrent.futures
    detected = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(LOCAL_PROBES)) as pool:
        futures = [pool.submit(probe_local_engine, p, timeout) for p in LOCAL_PROBES]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res:
                detected.append(res)
    detected.sort(key=lambda x: (x["type"], x["url"]))
    return detected

