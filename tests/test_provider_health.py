import uuid
import pytest
from workbench import server
from workbench.store import CIPHER, get, put


def connection():
    ident = str(uuid.uuid4())
    return put("providers", {"id": ident, "name": "Fixture health", "type": "compatible", "url": "http://fixture/v1", "secret": CIPHER.encrypt(b"fixture-health-key").decode(), "models": [{"id": "manual-only", "source": "manual", "tools": None, "vision": None, "streaming": None}]})


def test_discovery_records_health_and_keeps_last_good_models(monkeypatch):
    provider = connection()

    class Successful:
        def discover(self):
            return [{"id": "found", "source": "discovered", "tools": None, "vision": None, "streaming": None}]

    monkeypatch.setattr(server, "adapter", lambda item: Successful())
    server.discover(provider["id"])
    saved = get("providers", provider["id"])
    assert [model["id"] for model in saved["models"]] == ["found", "manual-only"]
    assert saved["last_discovery"]["ok"] is True
    assert saved["last_discovery"]["count"] == 1
    assert saved["last_discovery"]["latency_ms"] >= 0

    class Failing:
        def discover(self):
            raise ValueError("Provider returned HTTP 429; check endpoint, model availability and quota.")

    monkeypatch.setattr(server, "adapter", lambda item: Failing())
    with pytest.raises(ValueError, match="429"):
        server.discover(provider["id"])
    saved = get("providers", provider["id"])
    assert [model["id"] for model in saved["models"]] == ["found", "manual-only"]
    assert saved["last_discovery"]["ok"] is False
    assert "429" in saved["last_discovery"]["message"]


def test_connection_edit_invalidates_health_and_stale_discovery(monkeypatch):
    provider = connection()

    class ChangedDuringCheck:
        def discover(self):
            changed = get("providers", provider["id"])
            changed["url"] = "http://new-fixture/v1"
            put("providers", changed)
            return [{"id": "old-model", "source": "discovered"}]

    monkeypatch.setattr(server, "adapter", lambda item: ChangedDuringCheck())
    with pytest.raises(ValueError, match="changed during the check"):
        server.discover(provider["id"])
    assert get("providers", provider["id"])["models"][0]["id"] == "manual-only"
    edited = server.save_provider({"id": provider["id"], "name": "Edited", "type": "compatible", "url": "http://newer-fixture/v1"})
    assert edited["last_discovery"] is None
    assert edited["last_test"] is None


def test_inference_check_records_latency_and_redacted_failure(monkeypatch):
    import openhands.sdk

    provider = connection()

    class Config:
        def llm_config(self, model):
            return {"model": model}

    monkeypatch.setattr(server, "adapter", lambda item: Config())

    class Working:
        def __init__(self, **kwargs):
            pass
        def completion(self, **kwargs):
            return object()

    monkeypatch.setattr(openhands.sdk, "LLM", Working)
    server.test_provider(provider["id"], {"model": "fixture-model"})
    saved = get("providers", provider["id"])
    assert saved["last_test"]["ok"] is True
    assert saved["last_test"]["latency_ms"] >= 0

    class Failing(Working):
        def completion(self, **kwargs):
            raise ValueError("bad credential fixture-health-key")

    monkeypatch.setattr(openhands.sdk, "LLM", Failing)
    with pytest.raises(ValueError, match="Inference failed"):
        server.test_provider(provider["id"], {"model": "fixture-model"})
    saved = get("providers", provider["id"])
    assert saved["last_test"]["ok"] is False
    assert "fixture-health-key" not in saved["last_test"]["message"]
    assert "[REDACTED]" in saved["last_test"]["message"]
