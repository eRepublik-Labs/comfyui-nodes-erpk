# ABOUTME: Tests the media_resolution widget on Gemini Vision and Gemini Detect.
# ABOUTME: Checks the widget sits last and optional, and that the chosen value reaches the request config.

"""
Google's media-resolution page lists low, medium and high for the request-wide
setting (ultra_high is per item only). Probed 2026-11-18 on gemini-4-carbon and
gemini-4-hydrogen: one 32x32 PNG cost 296 / 569 / 1129 prompt tokens at low /
medium / high, and 1129 with the field unset.
"""

import asyncio
from types import SimpleNamespace

import pytest
from google.genai import types

from erpk.gemini.gemini_api.client import GeminiClient
from erpk.gemini.nodes import GeminiDetect, GeminiVision

IMAGE_NODES = [GeminiVision, GeminiDetect]


def _media_input(node_cls):
    return [i for i in node_cls.define_schema().inputs if i.id == "media_resolution"][0]


@pytest.mark.parametrize("node_cls", IMAGE_NODES)
def test_widget_offers_the_request_wide_levels(node_cls):
    widget = _media_input(node_cls)
    assert widget.options == ["default", "low", "medium", "high"]
    assert widget.default == "default"


@pytest.mark.parametrize("node_cls", IMAGE_NODES)
def test_widget_is_appended_last_and_optional(node_cls):
    # widgets_values is positional: anything but a trailing optional widget
    # shifts the values of saved workflows.
    inputs = node_cls.define_schema().inputs
    assert inputs[-1].id == "media_resolution"
    assert inputs[-1].optional is True


class _RecordingModels:
    def __init__(self):
        self.configs = []

    def generate_content(self, model, contents, config):
        self.configs.append(config)
        return types.GenerateContentResponse(candidates=[types.Candidate(
            content=types.Content(role="model", parts=[types.Part(text="[]")]),
            finish_reason=types.FinishReason.STOP)])


def _recording_client():
    client = GeminiClient(api_key="test-key")
    client.client = SimpleNamespace(models=_RecordingModels())
    return client


def _image():
    torch = pytest.importorskip("torch")
    return torch.zeros(1, 8, 8, 3)


def _run(node_cls, client, **kwargs):
    if node_cls is GeminiVision:
        asyncio.run(GeminiVision.execute(image=_image(), prompt="Describe it.", client=client, **kwargs))
    else:
        asyncio.run(GeminiDetect.execute(image=_image(), objects="cat", client=client, **kwargs))


@pytest.mark.parametrize("node_cls", IMAGE_NODES)
@pytest.mark.parametrize("level, sent", [
    ("low", types.MediaResolution.MEDIA_RESOLUTION_LOW),
    ("medium", types.MediaResolution.MEDIA_RESOLUTION_MEDIUM),
    ("high", types.MediaResolution.MEDIA_RESOLUTION_HIGH),
])
def test_chosen_level_reaches_the_request(node_cls, level, sent):
    client = _recording_client()
    _run(node_cls, client, media_resolution=level)
    assert client.client.models.configs[0].media_resolution == sent


@pytest.mark.parametrize("node_cls", IMAGE_NODES)
def test_default_sends_no_media_resolution(node_cls):
    client = _recording_client()
    _run(node_cls, client, media_resolution="default")
    _run(node_cls, client)
    assert [c.media_resolution for c in client.client.models.configs] == [None, None]
