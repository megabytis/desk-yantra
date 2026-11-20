import httpx
import pytest
from workbench.providers import adapter, public
from workbench.store import CIPHER


def connection(kind="compatible"):
    return {"type":kind,"url":"http://fixture/v1","secret":CIPHER.encrypt(b"fixture-key").decode()}


def test_discovery_uses_connection_credentials_and_pagination(monkeypatch):
    requests = []
    def handle(request):
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(200,json={"data":[{"id":"first"}],"has_more":True,"last_id":"first"})
        return httpx.Response(200,json={"data":[{"id":"second"}]})
    original = httpx.Client
    monkeypatch.setattr(httpx,"Client",lambda **kwargs: original(transport=httpx.MockTransport(handle),**kwargs))
    result = adapter(connection()).discover()
    assert [model["id"] for model in result] == ["first","second"]
    assert requests[0].headers["authorization"] == "Bearer fixture-key"
    assert requests[1].url.params["after"] == "first"
    assert result[0]["tools"] is None
    assert "secret" not in public(connection())


def test_anthropic_and_gemini_headers_and_cursor(monkeypatch):
    for kind, header, payload in [("anthropic","x-api-key",{"data":[{"id":"claude"}]}),("gemini","x-goog-api-key",{"models":[{"name":"models/gemini"}]})]:
        def handle(request):
            assert request.headers[header] == "fixture-key"
            return httpx.Response(200,json=payload)
        original = httpx.Client
        with monkeypatch.context() as patch:
            patch.setattr(httpx,"Client",lambda **kwargs: original(transport=httpx.MockTransport(handle),**kwargs))
            assert adapter(connection(kind)).discover()[0]["id"] in ("claude","gemini")


def test_ollama_only_installed_models_and_known_capabilities(monkeypatch):
    def handle(request):
        return httpx.Response(200,json={"models":[{"name":"installed"}]} if request.method == "GET" else {"capabilities":["completion","tools"]})
    original = httpx.Client
    monkeypatch.setattr(httpx,"Client",lambda **kwargs: original(transport=httpx.MockTransport(handle),**kwargs))
    models = adapter(connection("ollama")).discover()
    assert len(models) == 1
    assert models[0]["tools"] is True
    assert models[0]["vision"] is False


@pytest.mark.parametrize("status",[401,403,429,500])
def test_discovery_errors_do_not_echo_provider_body(monkeypatch,status):
    original = httpx.Client
    monkeypatch.setattr(httpx,"Client",lambda **kwargs: original(transport=httpx.MockTransport(lambda request:httpx.Response(status,text="private body")),**kwargs))
    with pytest.raises(ValueError) as error:
        adapter(connection()).discover()
    assert "private body" not in str(error.value)
