# ABOUTME: SSRF-hardened HTTP(S) byte fetcher with IP blocklist and size cap.
# ABOUTME: Used by node code that fetches user-supplied URLs to avoid private-network leaks.

import ipaddress
import socket
import urllib.request
from contextlib import contextmanager
from urllib.parse import urlparse

ALLOWED_SCHEMES = frozenset({"http", "https"})

# IP ranges blocked for outbound SSRF defense. Covers loopback, RFC 1918
# private, link-local (incl. cloud instance metadata at 169.254.169.254),
# CGN, IETF/reserved, multicast, broadcast, and IPv6 equivalents.
_BLOCKED_NETWORKS = [
    ipaddress.ip_network(n) for n in (
        "0.0.0.0/8",
        "10.0.0.0/8",
        "100.64.0.0/10",
        "127.0.0.0/8",
        "169.254.0.0/16",
        "172.16.0.0/12",
        "192.0.0.0/24",
        "192.168.0.0/16",
        "198.18.0.0/15",
        "224.0.0.0/4",
        "240.0.0.0/4",
        "255.255.255.255/32",
        "::1/128",
        "fc00::/7",
        "fe80::/10",
        "ff00::/8",
    )
]


def _is_blocked_ip(ip_str):
    """True if ip_str is in a blocked range or cannot be parsed."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    return any(ip in net for net in _BLOCKED_NETWORKS)


def _validate_url(url):
    """Reject by scheme, missing host, unresolvable host, or blocked IP.

    Returns the parsed URL on success; raises ValueError otherwise.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"Disallowed scheme: {parsed.scheme!r}")

    host = parsed.hostname
    if not host:
        raise ValueError("URL has no hostname")

    try:
        infos = socket.getaddrinfo(host, parsed.port, proto=socket.IPPROTO_TCP)
    except (socket.gaierror, OSError):
        raise ValueError(f"Cannot resolve host: {host}")

    for info in infos:
        ip = info[4][0]
        if _is_blocked_ip(ip):
            raise ValueError(f"Host {host} resolves to blocked address {ip}")

    return parsed


class _ValidatingRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Revalidate the destination URL on every redirect step.

    urllib follows Location: headers blindly by default; the most common
    SSRF chain in the wild is "benign URL redirects to 169.254.169.254".
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


@contextmanager
def safe_image_decode(max_pixels: int = 100_000_000):
    """Temporarily lower PIL.Image.MAX_IMAGE_PIXELS to guard against
    decompression-bomb images during decode.

    PIL's default threshold (~89M pixels) warns but allows decode up to 2x;
    inside this context manager, anything past max_pixels raises
    DecompressionBombError. The previous value is restored on exit.

    No-op if PIL is not installed.
    """
    try:
        from PIL import Image
    except ImportError:
        yield
        return
    original = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = max_pixels
    try:
        yield
    finally:
        Image.MAX_IMAGE_PIXELS = original


def fetch_remote_bytes(url, *, max_bytes, timeout=30, user_agent="ERPK/1.0"):
    """Fetch http(s) URL bytes with SSRF protection and a size cap.

    Args:
        url: HTTP/HTTPS URL to fetch.
        max_bytes: Maximum response size in bytes (required, no default).
        timeout: Per-request timeout in seconds.
        user_agent: User-Agent header value.

    Returns:
        bytes: response body, length <= max_bytes.

    Raises:
        ValueError: scheme/host/IP policy violation.
        IOError: response exceeded max_bytes, or network failure.
    """
    _validate_url(url)

    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    opener = urllib.request.build_opener(_ValidatingRedirectHandler())

    with opener.open(req, timeout=timeout) as resp:
        chunks = []
        total = 0
        while True:
            remaining = max_bytes - total + 1
            chunk = resp.read(min(64 * 1024, remaining))
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise IOError(f"Response exceeded {max_bytes} bytes")
            chunks.append(chunk)
        return b"".join(chunks)
