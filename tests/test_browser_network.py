import importlib.util
from pathlib import Path
import pytest
from workbench import server, companion
from workbench.store import put


spec = importlib.util.spec_from_file_location(
    "sandbox_browser_service", Path(__file__).resolve().parents[1] / "sandbox" / "browser_service.py"
)
service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service)


class Route:
    def __init__(self, url):
        self.request = type("Request", (), {"url": url})()
        self.result = None

    def continue_(self):
        self.result = "continued"

    def abort(self):
        self.result = "aborted"


def test_browser_requests_recheck_redirects_and_subresources():
    service.policy.update(domains=["example.com"], blocked=[])
    for url, expected in [
        ("https://example.com/start", "continued"),
        ("https://www.example.com/image.png", "continued"),
        ("https://evil.example/redirect", "aborted"),
        ("http://169.254.169.254/latest/meta-data/", "aborted"),
        ("file:///etc/passwd", "aborted"),
    ]:
        route = Route(url)
        service.guard_request(route)
        assert route.result == expected
    assert len(service.policy["blocked"]) == 3


def test_browser_requests_without_allowlist_still_block_metadata():
    assert service.allowed_request("https://example.org", [])
    assert not service.allowed_request("http://metadata.google.internal/", [])
    assert not service.allowed_request("http://[fd00:ec2::254]/", [])


def test_workspace_domain_rule_reaches_sandbox_browser(monkeypatch, tmp_path):
    grant = server.grant({"mode": "sandbox", "root": str(tmp_path), "shared": "", "capabilities": ["browser"], "allowed_domains": "example.com, *.python.org"})
    assert grant["allowed_domains"] == ["example.com", "*.python.org"]
    with pytest.raises(ValueError, match="domain names"):
        server.grant({"mode": "sandbox", "root": str(tmp_path), "shared": "", "capabilities": ["browser"], "allowed_domains": "https://example.com"})
    run = {"id": "network-policy-run", "grant": grant["id"], "mode": "sandbox", "status": "running", "tools": ["browser"]}
    put("runs", run)
    captured = {}
    def fake_subprocess(args, **kwargs):
        if args[:2] == ["docker", "inspect"]:
            return type("Result", (), {"returncode": 0})()
        captured["action"] = __import__("json").loads(args[-1])
        return {"exit_status": 0, "output": "ok"}
    monkeypatch.setattr(companion.subprocess, "run", fake_subprocess)
    monkeypatch.setattr(companion, "command", lambda run, args, cwd, action: fake_subprocess(args))
    companion.sandbox(run, {"op": "browser", "url": "https://example.com"})
    assert captured["action"]["allowed_domains"] == grant["allowed_domains"]
