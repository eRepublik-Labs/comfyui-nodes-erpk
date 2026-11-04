# ABOUTME: Tests that every Gemini request carries the client's system instruction and safety settings.
# ABOUTME: Covers text, both chat paths and both image nodes, recording the config at the SDK boundary.

"""
GeminiSystemInstruction and GeminiSafetySettings store their values on the
client. Each request a node sends must carry them. Chat is the trap: the SDK's
Chat.send_message uses the per-message config INSTEAD of the session config
(google-genai chats.py:257, `config if config else self._config`), so the
instruction set at start_chat never reached the model (measured 2026-11-03: a
random token in the system instruction came back from Text, not from Chat).
"""

import asyncio
from types import SimpleNamespace

import pytest
from google import genai
from google.genai import types

from erpk.gemini.gemini_api.client import GeminiClient
from erpk.gemini.nodes import (
    GeminiChat,
    GeminiImageEdit,
    GeminiImageGeneration,
    GeminiTextGeneration,
)

SYSTEM = "Answer in French."
SAFETY = [types.SafetySetting(category="HARM_CATEGORY_HARASSMENT",
                              threshold="BLOCK_LOW_AND_ABOVE")]


def _response(parts):
    return types.GenerateContentResponse(candidates=[types.Candidate(
        content=types.Content(role="model", parts=parts),
        finish_reason=types.FinishReason.STOP,
    )])


def _png_bytes():
    import io
    from PIL import Image
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "red").save(buffer, "PNG")
    return buffer.getvalue()


class _RecordingModels:
    """Stands in for genai.Client.models: records each config sent."""

    def __init__(self, response):
        self.response = response
        self.configs = []

    def generate_content(self, model, contents, config):
        self.configs.append(config)
        return self.response


class _RecordingSession:
    """Stands in for an SDK Chat: records each per-message config sent."""

    def __init__(self):
        self.configs = []

    def send_message(self, message, config):
        self.configs.append(config)
        return _response([types.Part(text="OK")])


def _configured_client():
    client = GeminiClient(api_key="test-key")
    client.update_config(system_instruction=SYSTEM, safety_settings=SAFETY)
    return client


def _assert_carries_client_settings(config):
    assert config.system_instruction == SYSTEM
    assert config.safety_settings == SAFETY


def test_text_generation_request_carries_client_settings():
    client = _configured_client()
    models = _RecordingModels(_response([types.Part(text="OK")]))
    client.client = SimpleNamespace(models=models)
    asyncio.run(GeminiTextGeneration.execute(prompt="Hi", client=client))
    _assert_carries_client_settings(models.configs[0])


def test_continued_chat_turn_carries_client_settings():
    session = _RecordingSession()
    asyncio.run(GeminiChat.execute(prompt="Hi", client=_configured_client(),
                                   chat_session=session))
    _assert_carries_client_settings(session.configs[0])


def test_first_chat_turn_carries_client_settings():
    session = _RecordingSession()
    client = _configured_client()
    client.client = SimpleNamespace(chats=SimpleNamespace(
        create=lambda model, config: session))
    asyncio.run(GeminiChat.execute(prompt="Hi", client=client))
    _assert_carries_client_settings(session.configs[0])


@pytest.fixture
def image_models(monkeypatch):
    """Every genai.Client the image nodes build answers from one recorder."""
    pytest.importorskip("torch")
    models = _RecordingModels(_response([types.Part(
        inline_data=types.Blob(data=_png_bytes(), mime_type="image/png"))]))
    monkeypatch.setattr(genai, "Client", lambda **kwargs: SimpleNamespace(models=models))
    return models


def test_image_generation_request_carries_client_settings(image_models):
    asyncio.run(GeminiImageGeneration.execute(prompt="a red square",
                                              client=_configured_client()))
    _assert_carries_client_settings(image_models.configs[0])


def test_image_edit_request_carries_client_settings(image_models):
    import torch
    asyncio.run(GeminiImageEdit.execute(image=torch.zeros(1, 8, 8, 3),
                                        prompt="make it blue",
                                        client=_configured_client()))
    _assert_carries_client_settings(image_models.configs[0])
