import json
import uuid
import pytest
from workbench import server
from workbench.store import put, get


def fixture_run(mode="sandbox", status="paused"):
    ident = str(uuid.uuid4())
    put("grants", {"id": ident, "capabilities": ["browser"], "revoked": False})
    return put("runs", {"id": ident, "grant": ident, "mode": mode, "tools": ["browser"], "status": status})


def test_browser_control_accepts_tabs_and_scroll_operations(monkeypatch):
    run = fixture_run()
    received = []
    monkeypatch.setattr(
        server,
        "companion",
        lambda path, body: received.append((path, body)) or {
            "result": {
                "url": "https://example.com",
                "title": "Example",
                "tabs": [{"id": 0, "title": "Example", "url": "https://example.com", "active": True}],
                "active_tab": 0,
                "text": "Example text",
                "elements": [
                    {
                        "index": 0,
                        "tag": "button",
                        "role": "button",
                        "selector": "button",
                        "text": "Submit",
                        "bounds": {"x": 100, "y": 200, "width": 80, "height": 30},
                    }
                ],
                "requires_user_takeover": False,
                "sensitive_fields": [],
                "screenshot": "browser.png",
            }
        },
    )

    # 1. new_tab
    res = server.browser_control(run["id"], {"operation": "new_tab", "url": "https://example.com/page2"})
    assert res["status"] == "paused"
    action = received[-1][1]
    assert action["browser_action"] == "new_tab"
    assert action["url"] == "https://example.com/page2"
    assert res["result"]["active_tab"] == 0

    # 2. switch_tab
    server.browser_control(run["id"], {"operation": "switch_tab", "tab_id": 1})
    action = received[-1][1]
    assert action["browser_action"] == "switch_tab"
    assert action["tab_id"] == 1

    # 3. close_tab
    server.browser_control(run["id"], {"operation": "close_tab", "tab_id": 1})
    action = received[-1][1]
    assert action["browser_action"] == "close_tab"
    assert action["tab_id"] == 1

    # 4. scroll
    server.browser_control(run["id"], {"operation": "scroll", "delta_y": 450})
    action = received[-1][1]
    assert action["browser_action"] == "scroll"
    assert action["delta_y"] == 450.0

    # 5. tabs
    server.browser_control(run["id"], {"operation": "tabs"})
    action = received[-1][1]
    assert action["browser_action"] == "tabs"


def test_browser_control_rejects_disallowed_urls_in_new_tab():
    run = fixture_run()
    with pytest.raises(ValueError, match="HTTP and HTTPS"):
        server.browser_control(run["id"], {"operation": "new_tab", "url": "javascript:alert(1)"})


def test_browser_service_multi_tab_and_dom_extraction():
    """Test browser_service module directly with simulated Playwright context/pages."""
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location(
        "sandbox_browser_service_unit",
        Path(__file__).resolve().parents[1] / "sandbox" / "browser_service.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Verify EXTRACT_DOM_SCRIPT is defined and checks interactive elements and security markers
    assert "button, a[href], input" in mod.EXTRACT_DOM_SCRIPT
    assert "has_captcha" in mod.EXTRACT_DOM_SCRIPT
    assert "has_password" in mod.EXTRACT_DOM_SCRIPT

    # Verify get_tabs_summary handles empty or multi-page state cleanly
    mod.browser_state["pages"] = []
    mod.browser_state["active_index"] = 0
    assert mod.get_tabs_summary() == []

    class MockPage:
        def __init__(self, title_val, url_val):
            self._title = title_val
            self._url = url_val
            self._closed = False

        def is_closed(self):
            return self._closed

        def title(self):
            return self._title

        @property
        def url(self):
            return self._url

        def close(self):
            self._closed = True

    p0 = MockPage("Tab One", "https://example.com/1")
    p1 = MockPage("Tab Two", "https://example.com/2")
    mod.browser_state["pages"] = [p0, p1]
    mod.browser_state["active_index"] = 1

    summary = mod.get_tabs_summary()
    assert len(summary) == 2
    assert summary[0]["title"] == "Tab One"
    assert not summary[0]["active"]
    assert summary[1]["title"] == "Tab Two"
    assert summary[1]["active"]

    # Close p1, check pruning
    p1.close()
    active = mod.get_active_page()
    assert active == p0
    assert mod.browser_state["active_index"] == 0

