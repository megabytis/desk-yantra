import uuid
import pytest
from workbench import server
from workbench.catalog import get_catalog, catalog_for_provider, find_catalog_model
from workbench.store import put, get


def test_catalog_structure_and_provider_types():
    catalog = get_catalog()
    expected_providers = {"openai", "anthropic", "gemini", "openrouter", "xai", "ollama", "lmstudio", "compatible"}
    assert expected_providers.issubset(set(catalog.keys()))
    
    for provider, models in catalog.items():
        assert len(models) > 0, f"Provider {provider} has no catalog models"
        for model in models:
            assert "id" in model
            assert "name" in model
            assert model["source"] == "catalog"
            assert "tools" in model
            assert "vision" in model
            assert "streaming" in model
            assert "context_window" in model
            assert model["context_window"] > 0
            assert "catalog_date" in model


def test_find_catalog_model():
    model = find_catalog_model("anthropic", "claude-3-7-sonnet-20250219")
    assert model is not None
    assert model["tools"] is True
    assert model["vision"] is True
    assert model["context_window"] == 200_000

    missing = find_catalog_model("anthropic", "non-existent-model")
    assert missing is None


def test_catalog_add_api():
    ident = str(uuid.uuid4())
    provider = put("providers", {
        "id": ident, "name": "Anthropic Test", "type": "anthropic",
        "url": "https://api.anthropic.com/v1", "secret": "", "models": []
    })

    # Add model from catalog
    res = server.add_catalog_model(ident, {"model": "claude-3-7-sonnet-20250219"})
    saved = get("providers", ident)
    assert len(saved["models"]) == 1
    added = saved["models"][0]
    assert added["id"] == "claude-3-7-sonnet-20250219"
    assert added["source"] == "catalog"
    assert added["tools"] is True
    assert added["vision"] is True
    assert added["context_window"] == 200_000

    # Adding again is idempotent (no duplicates)
    server.add_catalog_model(ident, {"model": "claude-3-7-sonnet-20250219"})
    assert len(get("providers", ident)["models"]) == 1


def test_catalog_models_preserved_during_discovery(monkeypatch):
    ident = str(uuid.uuid4())
    provider = put("providers", {
        "id": ident, "name": "Test Provider", "type": "compatible",
        "url": "http://127.0.0.1:8000/v1", "secret": "", "models": [
            {"id": "catalog-saved", "source": "catalog", "tools": True, "vision": False}
        ]
    })

    class MockAdapter:
        def discover(self):
            return [{"id": "discovered-model", "source": "discovered", "tools": None, "vision": None, "streaming": None}]

    monkeypatch.setattr(server, "adapter", lambda p: MockAdapter())
    server.discover(ident)

    saved = get("providers", ident)
    model_ids = [m["id"] for m in saved["models"]]
    assert "discovered-model" in model_ids
    assert "catalog-saved" in model_ids

