# ABOUTME: Gates the shared-workflow write routes behind a per-process token
# ABOUTME: and a same-origin check, so a cross-site page cannot write or delete files.

import hmac
import secrets
from urllib.parse import urlsplit

TOKEN_HEADER = "X-ERPK-Write-Token"

_TOKEN = secrets.token_urlsafe(32)


def write_token() -> str:
    """The token the page must echo back on every write or delete request.

    Only same-origin scripts can read it, because the endpoint that serves it
    is subject to the browser's same-origin policy and ComfyUI sends no CORS
    headers unless explicitly enabled.
    """
    return _TOKEN


def check_write_request(headers) -> None:
    """Raise PermissionError unless the request carries the token and comes
    from the page's own origin.

    The token alone stops a cross-site page, which can send a request but
    cannot read the token. The origin checks close the case where a
    misconfigured CORS or proxy setup leaks it.
    """
    presented = headers.get(TOKEN_HEADER)
    if presented is None:
        raise PermissionError(f"Missing {TOKEN_HEADER} header")
    if not hmac.compare_digest(presented, _TOKEN):
        raise PermissionError(f"Invalid {TOKEN_HEADER}")
    if headers.get("Sec-Fetch-Site") == "cross-site":
        raise PermissionError("Cross-site request refused")
    origin = headers.get("Origin")
    host = headers.get("Host")
    if origin and host:
        origin_host = urlsplit(origin).netloc.lower()
        if origin_host != host.lower():
            raise PermissionError(f"Origin {origin_host} does not match host {host}")
