import ipaddress
import urllib.parse
from typing import Iterable

BLOCKED_SCHEMES = {"javascript", "file", "data", "vbscript", "chrome", "edge", "about", "gopher"}
METADATA_IPS = {"169.254.169.254", "fd00:ec2::254"}
METADATA_HOSTS = {"metadata.google.internal", "metadata.aws.internal"}


def validate_browser_url(url: str, allowed_domains: Iterable[str] | None = None) -> tuple[bool, str]:
    """Validate a target URL against browser navigation security policy.
    Adapted from browser-use security watchdog and domain rules.
    """
    cleaned = (url or "").strip()
    if not cleaned or cleaned in ("about:blank", "about:blank#"):
        return True, ""

    try:
        parsed = urllib.parse.urlsplit(cleaned)
    except Exception as err:
        return False, f"Malformed URL: {err}"

    scheme = parsed.scheme.lower()
    if scheme in BLOCKED_SCHEMES or scheme not in ("http", "https"):
        return False, f"Navigation scheme '{scheme}:' is blocked. Only http:// and https:// URLs are allowed."

    host = (parsed.hostname or "").strip().lower()
    if not host:
        return False, "URL lacks a valid hostname."

    if host in METADATA_HOSTS:
        return False, f"Access to cloud metadata host '{host}' is prohibited."

    # Check IP addresses
    try:
        ip = ipaddress.ip_address(host)
        if str(ip) in METADATA_IPS or ip.is_link_local:
            return False, f"Access to link-local/cloud metadata IP '{host}' is prohibited."
    except ValueError:
        pass

    # If allowed_domains is provided, enforce it
    if allowed_domains:
        def domain_match(pattern: str, target: str) -> bool:
            pattern = pattern.strip().lower()
            if pattern.startswith("*."):
                suffix = pattern[2:]
                return target == suffix or target.endswith("." + suffix)
            return target == pattern or target == "www." + pattern

        matched = any(domain_match(d, host) for d in allowed_domains if d and d.strip())
        if not matched:
            return False, f"Host '{host}' is not in the authorized domain list for this workspace."

    return True, ""

