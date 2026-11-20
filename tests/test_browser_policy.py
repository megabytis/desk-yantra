import pytest
from workbench.browser_policy import validate_browser_url
from workbench import companion
from workbench.store import put, get


def test_validate_browser_url_blocked_schemes():
    for blocked in [
        "javascript:alert(1)",
        "file:///etc/passwd",
        "data:text/html,<h1>Hello</h1>",
        "vbscript:msgbox(1)",
        "chrome://settings",
        "edge://flags",
        "gopher://example.com",
    ]:
        ok, reason = validate_browser_url(blocked)
        assert not ok, f"Expected {blocked} to be blocked"
        assert "blocked" in reason.lower() or "only http" in reason.lower()


def test_validate_browser_url_cloud_metadata_protection():
    for metadata_url in [
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://metadata.aws.internal",
    ]:
        ok, reason = validate_browser_url(metadata_url)
        assert not ok, f"Expected {metadata_url} to be blocked"
        assert "prohibited" in reason.lower() or "metadata" in reason.lower()


def test_validate_browser_url_allowed_urls():
    for allowed in [
        "about:blank",
        "https://example.com",
        "https://github.com/torvalds/linux",
        "http://localhost:8080/app",
        "https://sub.domain.org/path?query=1#frag",
    ]:
        ok, reason = validate_browser_url(allowed)
        assert ok, f"Expected {allowed} to be allowed, got: {reason}"


def test_validate_browser_url_domain_whitelist():
    allowed_domains = ["github.com", "*.python.org"]

    ok, _ = validate_browser_url("https://github.com/login", allowed_domains)
    assert ok

    ok, _ = validate_browser_url("https://www.github.com/about", allowed_domains)
    assert ok

    ok, _ = validate_browser_url("https://docs.python.org/3/", allowed_domains)
    assert ok

    ok, reason = validate_browser_url("https://evil.com", allowed_domains)
    assert not ok
    assert "not in the authorized domain list" in reason


def test_companion_blocks_prohibited_browser_navigation():
    run_id = "test-browser-policy-run"
    grant_id = "test-browser-policy-grant"

    put("grants", {
        "id": grant_id,
        "mode": "sandbox",
        "capabilities": ["browser"],
        "revoked": False,
    })
    put("runs", {
        "id": run_id,
        "grant": grant_id,
        "mode": "sandbox",
        "status": "running",
        "tools": ["browser"],
    })

    action = {
        "op": "browser",
        "url": "file:///etc/shadow",
    }

    with pytest.raises(ValueError, match="Browser navigation blocked by policy"):
        companion.check(get("runs", run_id), action)
