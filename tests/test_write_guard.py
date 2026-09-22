# ABOUTME: Tests the token gate on the shared-workflow write routes.
# ABOUTME: A request must carry the per-process token and come from the page's own origin.

import pytest

from write_guard import TOKEN_HEADER, check_write_request, write_token


def test_token_is_stable_and_long():
    first = write_token()
    assert first == write_token()
    assert len(first) >= 43  # token_urlsafe(32) encodes to 43 characters


def test_missing_token_header_is_rejected():
    with pytest.raises(PermissionError, match=f"^Missing {TOKEN_HEADER} header$"):
        check_write_request({"Host": "localhost:8188"})


def test_wrong_token_is_rejected():
    with pytest.raises(PermissionError, match=f"^Invalid {TOKEN_HEADER}$"):
        check_write_request({"Host": "localhost:8188", TOKEN_HEADER: "not-the-token"})


def test_origin_host_mismatch_is_rejected():
    headers = {
        "Host": "comfy.internal:8188",
        "Origin": "https://evil.example",
        TOKEN_HEADER: write_token(),
    }
    with pytest.raises(PermissionError, match="^Origin evil.example does not match host comfy.internal:8188$"):
        check_write_request(headers)


def test_cross_site_fetch_is_rejected():
    headers = {
        "Host": "comfy.internal:8188",
        "Sec-Fetch-Site": "cross-site",
        TOKEN_HEADER: write_token(),
    }
    with pytest.raises(PermissionError, match="^Cross-site request refused$"):
        check_write_request(headers)


def test_same_origin_request_is_allowed():
    headers = {
        "Host": "comfy.internal:8188",
        "Origin": "http://comfy.internal:8188",
        "Sec-Fetch-Site": "same-origin",
        TOKEN_HEADER: write_token(),
    }
    assert check_write_request(headers) is None


def test_request_without_origin_headers_is_allowed_with_token():
    # curl and same-machine tooling send neither Origin nor Sec-Fetch-Site;
    # the token is the proof.
    assert check_write_request({"Host": "localhost:8188", TOKEN_HEADER: write_token()}) is None
