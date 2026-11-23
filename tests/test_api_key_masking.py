# ABOUTME: A resolved API key travels between nodes as an ApiKey, which prints and serializes masked,
# ABOUTME: while every API client still sends the real key. Sinks: Preview Anything, PreviewAny, history.

import asyncio
import json

import pytest

from erpk.key_store import ApiKey

FAKE_KEY = "wsk-Q7zR2mPx9LtV4nKc"


def assert_masked(text):
    """No four-character run of FAKE_KEY appears, so a last-four style mask fails too."""
    windows = [FAKE_KEY[i:i + 4] for i in range(len(FAKE_KEY) - 3)]
    assert [w for w in windows if w in text] == []


def test_reveal_returns_the_key():
    assert ApiKey(FAKE_KEY).reveal() == FAKE_KEY


def test_str_repr_and_format_are_masked():
    key = ApiKey(FAKE_KEY)

    assert str(key) == "ApiKey(set)"
    assert repr(key) == "ApiKey(set)"
    assert f"Bearer {key}" == "Bearer ApiKey(set)"
    assert_masked(str({"api_key": key}))


def test_json_dumps_refuses_the_key():
    with pytest.raises(TypeError):
        json.dumps({"api_key": ApiKey(FAKE_KEY)})


def test_an_empty_or_non_string_key_is_refused():
    with pytest.raises(ValueError, match="^API key is empty$"):
        ApiKey("")
    with pytest.raises(TypeError, match="^API key must be a str, got int$"):
        ApiKey(1234)


# ---------------------------------------------------------------------------
# Each API client takes an ApiKey and sends the real key.
# ---------------------------------------------------------------------------


class _Response:
    status_code = 200

    def json(self):
        return {"code": 200, "data": {"status": "completed"}}


class _RecordingSession:
    def __init__(self):
        self.headers = []

    def get(self, url, headers=None, **kwargs):
        self.headers.append(headers)
        return _Response()


def test_wavespeed_client_sends_the_revealed_key():
    from erpk.wavespeed.wavespeed_api.client import WaveSpeedClient

    client = WaveSpeedClient(ApiKey(FAKE_KEY))
    client.session = session = _RecordingSession()
    asyncio.run(client.get("/api/v3/predictions/req-1/result"))

    assert session.headers[0]["Authorization"] == f"Bearer {FAKE_KEY}"


def test_byteplus_client_sends_the_revealed_key(tmp_path):
    from erpk.byteplus.byteplus_api.client import BytePlusClient

    sent = []

    def transport(method, url, headers, data, timeout):
        sent.append(headers)
        return 200, '{"id": "task-1", "status": "running"}'

    client = BytePlusClient(api_key=ApiKey(FAKE_KEY), config_path=str(tmp_path / "none.ini"),
                            transport=transport)
    asyncio.run(client.get_video_task("task-1"))

    assert sent[0]["Authorization"] == f"Bearer {FAKE_KEY}"


def test_grok_client_hands_the_sdk_the_revealed_key(monkeypatch, tmp_path):
    xai_sdk = pytest.importorskip("xai_sdk")
    from erpk.grok.grok_api.client import GrokClient

    seen = []
    monkeypatch.setattr(xai_sdk, "Client", lambda **kwargs: seen.append(kwargs["api_key"]))
    GrokClient(api_key=ApiKey(FAKE_KEY), config_path=str(tmp_path / "none.ini"))._ensure_client()

    assert seen == [FAKE_KEY]
    assert type(seen[0]) is str


# ---------------------------------------------------------------------------
# The client nodes output an ApiKey: every sink that stringifies the output
# shows it masked, and the nodes downstream still send the real key.
# ---------------------------------------------------------------------------


def _wavespeed_client_output():
    from erpk.wavespeed.nodes import WaveSpeedAIAPIClient
    return WaveSpeedAIAPIClient.execute(api_key=FAKE_KEY)[0]


def _grok_client_output():
    from erpk.grok.nodes import GrokAPIClient
    return GrokAPIClient.execute(api_key=FAKE_KEY)[0]


def _byteplus_client_output():
    from erpk.byteplus.nodes import BytePlusAPIClient
    return BytePlusAPIClient.execute(api_key=FAKE_KEY)[0]


CLIENT_OUTPUTS = [_wavespeed_client_output, _grok_client_output, _byteplus_client_output]


@pytest.mark.parametrize("client_output", CLIENT_OUTPUTS)
def test_client_node_output_is_masked_in_every_sink(client_output):
    from erpk.utils.preview_anything import _stringify

    output = client_output()

    assert_masked(str(output))
    assert_masked(repr(output))
    assert_masked(f"{output}")
    # ERPK Preview Anything: json.dumps(default=str).
    assert_masked(_stringify(output))
    # Core PreviewAny tries json.dumps, then falls back to str().
    with pytest.raises(TypeError):
        json.dumps(output, indent=4)


class _StopAtHTTP(Exception):
    pass


class _SessionStoppingAtPost:
    def __init__(self, sent):
        self.sent = sent

    def mount(self, prefix, adapter):
        pass

    def post(self, url, headers=None, **kwargs):
        self.sent.append(headers)
        raise _StopAtHTTP


def test_wavespeed_model_node_sends_the_real_key(monkeypatch):
    pytest.importorskip("torch")
    from erpk.wavespeed.flux_2_pro import Flux2ProNode
    from erpk.wavespeed.wavespeed_api import client as client_module

    sent = []
    monkeypatch.setattr(client_module.requests, "Session", lambda: _SessionStoppingAtPost(sent))

    with pytest.raises(_StopAtHTTP):
        asyncio.run(Flux2ProNode.execute(prompt="a red cube", client=_wavespeed_client_output()))

    assert sent[0]["Authorization"] == f"Bearer {FAKE_KEY}"


def test_grok_node_hands_the_sdk_the_real_key(monkeypatch):
    xai_sdk = pytest.importorskip("xai_sdk")
    from erpk.grok.nodes import GrokTextGeneration

    seen = []

    def client(**kwargs):
        seen.append(kwargs["api_key"])
        raise _StopAtHTTP

    monkeypatch.setattr(xai_sdk, "Client", client)

    with pytest.raises(ValueError, match="^Grok text generation failed: $"):
        asyncio.run(GrokTextGeneration.execute(prompt="Write about rivers.", client=_grok_client_output()))

    assert seen == [FAKE_KEY]


def test_byteplus_node_sends_the_real_key(monkeypatch):
    from erpk.byteplus.byteplus_api import client as client_module
    from erpk.byteplus.video_nodes import BytePlusSeedanceTaskResult

    sent = []

    def transport(method, url, headers, data, timeout):
        sent.append(headers)
        return 200, '{"id": "cgt-20261119021437-q68pg", "status": "running"}'

    output = _byteplus_client_output()
    monkeypatch.setattr(client_module, "_requests_transport", lambda session: transport)
    asyncio.run(BytePlusSeedanceTaskResult.execute(task_id="cgt-20261119021437-q68pg", wait=False,
                                                   client=output))

    assert sent[0]["Authorization"] == f"Bearer {FAKE_KEY}"
