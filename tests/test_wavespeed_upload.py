# ABOUTME: Tests WaveSpeedClient file upload against the v3 media API.
# ABOUTME: Covers the two-step ticket flow and that the API key never reaches storage.

import asyncio
import os
import sys

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO)

pytest.importorskip("requests")
Image = pytest.importorskip("PIL.Image")

from wavespeed.wavespeed_api.client import WaveSpeedClient


# Shape taken from the worked example at https://wavespeed.ai/docs/upload-files-api
TICKET = {
    "type": "image",
    "download_url": "https://cdn.example.com/media/abc123/image.png",
    "filename": "image.png",
    "size": 1024,
    "upload": {
        "method": "PUT",
        "url": "https://storage.example.invalid/signed-put?sig=xyz",
        "headers": {"Content-Type": "image/png", "If-None-Match": "*"},
        "expires_at": "2036-01-01T00:00:00Z",
    },
}


class _Response:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload


class _RecordingSession:
    """Stands in for requests.Session and records every call the client makes."""

    def __init__(self, ticket=TICKET):
        self.ticket = ticket
        self.posts = []
        self.puts = []

    def post(self, url, **kwargs):
        self.posts.append(dict(url=url, **kwargs))
        return _Response(200, {"code": 200, "message": "success", "data": self.ticket})

    def put(self, url, **kwargs):
        self.puts.append(dict(url=url, **kwargs))
        return _Response(200, {})


def _run_upload(session):
    client = WaveSpeedClient(api_key="test-key")
    client.session = session
    return asyncio.run(client.upload_file(Image.new("RGB", (8, 8), "red")))


def test_upload_requests_a_ticket_then_puts_the_bytes_to_storage():
    """Upload must use the two-step v3 flow rather than posting multipart through the gateway.

    Step one asks api.wavespeed.ai for an upload ticket describing where the
    bytes should go. Step two sends the bytes straight to that storage URL, so
    they never transit the API gateway.
    """
    session = _RecordingSession()

    download_url = _run_upload(session)

    assert len(session.posts) == 1, "expected exactly one ticket request"
    ticket_request = session.posts[0]
    assert ticket_request["url"] == "https://api.wavespeed.ai/api/v3/media/uploads"

    body = ticket_request.get("json")
    assert body is not None, "ticket request must send JSON, not multipart"
    assert body["filename"] == "image.png"
    assert body["content_type"] == "image/png"
    assert isinstance(body["size"], int) and body["size"] > 0

    assert len(session.puts) == 1, "expected exactly one storage upload"
    storage_call = session.puts[0]
    assert storage_call["url"] == TICKET["upload"]["url"]
    assert storage_call["headers"] == TICKET["upload"]["headers"]

    # The declared size must match the bytes actually sent, or storage rejects it.
    assert body["size"] == len(storage_call["data"])

    assert download_url == TICKET["download_url"]


def test_api_key_is_never_sent_to_storage():
    """The signed storage URL belongs to a third party and must never see our API key.

    The docs are explicit: send the key only to api.wavespeed.ai. The ticket
    request is authenticated; the PUT that follows carries only the headers the
    ticket handed back.
    """
    session = _RecordingSession()

    _run_upload(session)

    ticket_headers = session.posts[0]["headers"]
    assert ticket_headers["Authorization"] == "Bearer test-key", (
        "the ticket request is the one call that must authenticate"
    )

    storage_headers = session.puts[0]["headers"]
    leaked = [k for k in storage_headers if k.lower() == "authorization"]
    assert not leaked, f"API key leaked to storage via {leaked}"
    assert "test-key" not in str(storage_headers), "API key leaked into storage headers"


def test_task_result_is_polled_on_v3():
    """Every async node polls through this path, so it must be a supported one."""
    client = WaveSpeedClient(api_key="test-key")
    seen = {}

    async def _capture(endpoint, timeout=None):
        seen["endpoint"] = endpoint
        return {"status": "completed"}

    client.get = _capture
    asyncio.run(client.check_task_status("req-123"))

    assert seen["endpoint"] == "/api/v3/predictions/req-123/result"
