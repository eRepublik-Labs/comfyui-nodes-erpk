# ABOUTME: Tests for utils.safe_fetch — SSRF-hardened HTTP byte fetcher.
# ABOUTME: Covers scheme allowlist, IP blocklist, redirect revalidation, size cap.

import io
import pytest
from unittest.mock import MagicMock, patch


class TestIsBlockedIP:
    """The IP blocklist must cover loopback, private, link-local, multicast,
    reserved, and IPv6 equivalents — and reject anything unparseable."""

    @pytest.mark.parametrize("ip", [
        # IPv4 loopback
        "127.0.0.1",
        "127.5.5.5",
        # IPv4 private (RFC 1918)
        "10.0.0.1",
        "10.255.255.255",
        "172.16.0.1",
        "172.31.255.255",
        "192.168.0.1",
        "192.168.255.255",
        # CGN (RFC 6598)
        "100.64.0.1",
        # Link-local (incl AWS/GCP/Azure instance metadata endpoint)
        "169.254.169.254",
        "169.254.0.1",
        # Reserved
        "0.0.0.0",
        "240.0.0.1",
        "255.255.255.255",
        # Multicast
        "224.0.0.1",
        "239.255.255.255",
        # IPv6 loopback
        "::1",
        # IPv6 link-local
        "fe80::1",
        "fe80::abcd",
        # IPv6 unique local (private)
        "fc00::1",
        "fd00::1",
        # IPv6 multicast
        "ff00::1",
        "ff02::1",
    ])
    def test_blocks_known_bad_ip(self, ip):
        from utils.safe_fetch import _is_blocked_ip
        assert _is_blocked_ip(ip) is True

    @pytest.mark.parametrize("ip", [
        "8.8.8.8",                # Google DNS
        "1.1.1.1",                # Cloudflare DNS
        "93.184.216.34",          # example.com
        "2001:4860:4860::8888",   # Google DNS v6
    ])
    def test_allows_known_public_ip(self, ip):
        from utils.safe_fetch import _is_blocked_ip
        assert _is_blocked_ip(ip) is False

    def test_blocks_unparseable_ip(self):
        # Fail closed: if we can't parse it, we can't reason about it
        from utils.safe_fetch import _is_blocked_ip
        assert _is_blocked_ip("not-an-ip") is True


class TestValidateURL:
    """_validate_url checks scheme allowlist, resolves host via getaddrinfo,
    and rejects any URL whose resolved address is blocked."""

    def test_rejects_file_scheme(self):
        from utils.safe_fetch import _validate_url
        with pytest.raises(ValueError, match="scheme"):
            _validate_url("file:///etc/passwd")

    def test_rejects_javascript_scheme(self):
        from utils.safe_fetch import _validate_url
        with pytest.raises(ValueError, match="scheme"):
            _validate_url("javascript:alert(1)")

    def test_rejects_gopher_scheme(self):
        from utils.safe_fetch import _validate_url
        with pytest.raises(ValueError, match="scheme"):
            _validate_url("gopher://example.com/")

    def test_rejects_ftp_scheme(self):
        from utils.safe_fetch import _validate_url
        with pytest.raises(ValueError, match="scheme"):
            _validate_url("ftp://example.com/")

    def test_rejects_data_scheme(self):
        # data: URIs are handled separately by callers (no network needed),
        # so the SSRF fetcher must refuse them
        from utils.safe_fetch import _validate_url
        with pytest.raises(ValueError, match="scheme"):
            _validate_url("data:text/plain;base64,SGk=")

    def test_rejects_url_without_hostname(self):
        from utils.safe_fetch import _validate_url
        with pytest.raises(ValueError, match="host"):
            _validate_url("http:///path")

    @pytest.mark.parametrize("url", [
        "http://127.0.0.1/",
        "https://127.5.5.5/",
        "http://10.0.0.1/",
        "http://10.255.255.255/",
        "http://172.16.0.1/",
        "http://172.31.255.255/",
        "http://192.168.0.1/",
        # The AWS/GCP/Azure metadata endpoint — single most exploited SSRF target
        "http://169.254.169.254/latest/meta-data/",
        "http://0.0.0.0/",
        "http://255.255.255.255/",
        "http://[::1]/",
        "http://[fe80::1]/",
        "http://[fc00::1]/",
        "http://[ff00::1]/",
    ])
    def test_rejects_blocked_ip_address(self, url):
        from utils.safe_fetch import _validate_url
        with pytest.raises(ValueError, match="blocked"):
            _validate_url(url)

    def test_rejects_unresolvable_host(self):
        # .invalid is RFC 2606 reserved — guaranteed NXDOMAIN
        from utils.safe_fetch import _validate_url
        with pytest.raises(ValueError, match="resolve"):
            _validate_url("http://no-such-host.invalid/")

    def test_accepts_direct_public_ipv4(self):
        from utils.safe_fetch import _validate_url
        result = _validate_url("http://8.8.8.8/")
        assert result.scheme == "http"
        assert result.hostname == "8.8.8.8"

    def test_accepts_https(self):
        from utils.safe_fetch import _validate_url
        result = _validate_url("https://8.8.8.8/")
        assert result.scheme == "https"


class TestFetchRemoteBytes:
    """fetch_remote_bytes validates first, streams with a byte cap."""

    def test_rejects_blocked_url_before_network(self):
        # Should raise before any network call. Use a URL that's blocked at
        # the IP-validation stage; we don't mock urlopen, so a network call
        # would fail with ConnectionRefusedError, not ValueError.
        from utils.safe_fetch import fetch_remote_bytes
        with pytest.raises(ValueError):
            fetch_remote_bytes("http://127.0.0.1/", max_bytes=1024)

    def test_size_cap_enforced(self):
        from utils.safe_fetch import fetch_remote_bytes

        fake_bytes = b"x" * 5000

        class FakeResponse:
            def __init__(self):
                self._buf = io.BytesIO(fake_bytes)

            def read(self, n):
                return self._buf.read(n)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        with patch("utils.safe_fetch._validate_url"), \
             patch("urllib.request.OpenerDirector.open", return_value=FakeResponse()):
            with pytest.raises(IOError, match="exceeded"):
                fetch_remote_bytes("http://example.com/", max_bytes=1000)

    def test_happy_path_returns_bytes(self):
        from utils.safe_fetch import fetch_remote_bytes

        fake_bytes = b"hello world"

        class FakeResponse:
            def __init__(self):
                self._buf = io.BytesIO(fake_bytes)

            def read(self, n):
                return self._buf.read(n)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        with patch("utils.safe_fetch._validate_url"), \
             patch("urllib.request.OpenerDirector.open", return_value=FakeResponse()):
            result = fetch_remote_bytes("http://example.com/", max_bytes=1000)
            assert result == fake_bytes

    def test_sends_user_agent(self):
        from utils.safe_fetch import fetch_remote_bytes

        captured_req = {}

        class FakeResponse:
            def __init__(self):
                self._buf = io.BytesIO(b"")

            def read(self, n):
                return self._buf.read(n)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        def fake_open(self_, req, timeout=None):
            captured_req["url"] = req.full_url
            captured_req["ua"] = req.get_header("User-agent")
            return FakeResponse()

        with patch("utils.safe_fetch._validate_url"), \
             patch("urllib.request.OpenerDirector.open", new=fake_open):
            fetch_remote_bytes("http://example.com/", max_bytes=1000,
                               user_agent="ERPK-Test/9.9")
            assert captured_req["ua"] == "ERPK-Test/9.9"


class TestSafeImageDecode:
    """safe_image_decode() lowers PIL.Image.MAX_IMAGE_PIXELS during a decode
    to make decompression-bomb images raise instead of warn."""

    def test_lowers_max_pixels_inside_context(self):
        pil = pytest.importorskip("PIL.Image")
        from utils.safe_fetch import safe_image_decode

        original = pil.MAX_IMAGE_PIXELS
        with safe_image_decode(max_pixels=1234):
            assert pil.MAX_IMAGE_PIXELS == 1234
        assert pil.MAX_IMAGE_PIXELS == original

    def test_restores_max_pixels_on_exception(self):
        pil = pytest.importorskip("PIL.Image")
        from utils.safe_fetch import safe_image_decode

        original = pil.MAX_IMAGE_PIXELS
        with pytest.raises(RuntimeError):
            with safe_image_decode(max_pixels=1234):
                raise RuntimeError("simulated decode failure")
        assert pil.MAX_IMAGE_PIXELS == original

    def test_no_op_when_pil_unavailable(self, monkeypatch):
        import sys
        from utils.safe_fetch import safe_image_decode

        # Simulate PIL not installed
        monkeypatch.setitem(sys.modules, "PIL", None)
        # Must not raise — caller can use the context manager defensively
        with safe_image_decode():
            pass


class TestValidatingRedirectHandler:
    """The redirect handler must revalidate the destination URL before
    allowing urllib to follow the redirect."""

    def test_blocks_redirect_to_private_ip(self):
        from utils.safe_fetch import _ValidatingRedirectHandler

        handler = _ValidatingRedirectHandler()
        req = MagicMock()
        with pytest.raises(ValueError):
            handler.redirect_request(
                req, fp=None, code=302, msg="Found", headers={},
                newurl="http://127.0.0.1/admin",
            )

    def test_blocks_redirect_to_aws_metadata(self):
        from utils.safe_fetch import _ValidatingRedirectHandler

        handler = _ValidatingRedirectHandler()
        req = MagicMock()
        with pytest.raises(ValueError):
            handler.redirect_request(
                req, fp=None, code=302, msg="Found", headers={},
                newurl="http://169.254.169.254/latest/meta-data/",
            )

    def test_blocks_redirect_to_file_scheme(self):
        from utils.safe_fetch import _ValidatingRedirectHandler

        handler = _ValidatingRedirectHandler()
        req = MagicMock()
        with pytest.raises(ValueError):
            handler.redirect_request(
                req, fp=None, code=302, msg="Found", headers={},
                newurl="file:///etc/passwd",
            )
