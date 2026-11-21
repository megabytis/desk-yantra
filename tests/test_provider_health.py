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


def test_key_rotation_and_removal_preserve_connection_history():
    provider = connection()
    ident = provider["id"]
    put("runs", {"id": str(uuid.uuid4()), "connection": ident, "model": "manual-only", "status": "completed"})
    provider["last_test"] = {"ok": True, "model": "manual-only"}
    provider["last_discovery"] = {"ok": True, "count": 1}
    provider["models"].append({"id": "account-discovered", "source": "discovered"})
    put("providers", provider)
    original_secret = provider["secret"]

    rotated = server.save_provider({"id": ident, "name": "Fixture health", "type": "compatible", "url": provider["url"], "key": "new-secret"})
    assert rotated["id"] == ident and rotated["has_key"] is True
    assert "secret" not in rotated
    assert get("providers", ident)["secret"] != original_secret
    assert rotated["last_test"] is None and rotated["last_discovery"] is None
    assert [item["id"] for item in rotated["models"]] == ["manual-only"]

    with pytest.raises(ValueError, match="either a replacement key or remove"):
        server.save_provider({"id": ident, "name": "Fixture health", "type": "compatible", "url": provider["url"], "key": "both", "remove_key": True})
    removed = server.save_provider({"id": ident, "name": "Fixture health", "type": "compatible", "url": provider["url"], "remove_key": True})
    assert removed["id"] == ident and removed["has_key"] is False
    assert get("providers", ident)["secret"] == ""
    assert [item["id"] for item in removed["models"]] == ["manual-only"]
    with pytest.raises(ValueError, match="changed during the check"):
        server.record_provider_check(provider, "last_test", {"ok": True})
    assert any(run.get("connection") == ident for run in server.all_objects("runs"))
