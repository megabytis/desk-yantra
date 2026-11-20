import httpx
import pytest
from unittest.mock import MagicMock, patch
from workbench.providers import probe_local_engine, detect_local_engines, LOCAL_PROBES
from workbench import server


def test_probe_local_engine_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "models": [{"name": "qwen2.5:latest"}, {"name": "llama3.2:3b"}]
    }

    probe = LOCAL_PROBES[0]  # Ollama
    with patch("httpx.Client.get", return_value=mock_resp):
        res = probe_local_engine(probe, timeout=0.5)
        assert res is not None
        assert res["detected"] is True
        assert res["type"] == "ollama"
        assert res["model_count"] == 2
        assert "qwen2.5:latest" in res["models"]
        assert res["latency_ms"] >= 0


def test_probe_local_engine_connection_failure():
    probe = LOCAL_PROBES[0]
    with patch("httpx.Client.get", side_effect=httpx.ConnectError("Connection refused")):
        res = probe_local_engine(probe, timeout=0.1)
        assert res is None


def test_detect_local_engines_mixed():
    def fake_get(url, *args, **kwargs):
        resp = MagicMock()
        if "11434" in url:
            resp.status_code = 200
            resp.json.return_value = {"models": [{"name": "ollama-model-1"}]}
            return resp
        elif "1234" in url:
            resp.status_code = 200
            resp.json.return_value = {"data": [{"id": "lmstudio-model-1"}]}
            return resp
        raise httpx.ConnectError("Refused")

    with patch("httpx.Client.get", side_effect=fake_get):
        detected = detect_local_engines(timeout=0.5)
        assert len(detected) == 2
        types = {d["type"] for d in detected}
        assert types == {"ollama", "lmstudio"}


def test_api_detect_local_endpoint():
    with patch("workbench.server.detect_local_engines") as mock_detect:
        mock_detect.return_value = [
            {"type": "ollama", "name": "Ollama", "url": "http://127.0.0.1:11434", "detected": True, "latency_ms": 5, "model_count": 1, "models": ["test-model"]}
        ]
        result = server.api_detect_local()
        assert "engines" in result
        assert len(result["engines"]) == 1
        assert result["engines"][0]["name"] == "Ollama"

