# ABOUTME: Tests for OpenAI image generation API parameter construction
# ABOUTME: Ensures response_format is only sent for models that support it

import sys
from unittest.mock import MagicMock, patch

import pytest

# In the test environment, our local openai/ package shadows the SDK's openai package.
# The client does `from openai import APIError` (lazy import inside methods), which
# resolves to our local package. Inject a mock APIError so the import succeeds.
import openai as _local_openai
if not hasattr(_local_openai, "APIError"):
    _local_openai.APIError = type("APIError", (Exception,), {})

from openai.openai_api.client import OpenAIClient


GPT_IMAGE_MODELS = ["gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini"]
DALLE_MODELS = ["dall-e-3", "dall-e-2"]


def _make_client_with_mock():
    """Create an OpenAIClient with a mocked SDK client."""
    client = OpenAIClient.__new__(OpenAIClient)
    mock_openai = MagicMock()
    mock_img = MagicMock()
    mock_img.b64_json = "fakebase64data"
    mock_img.revised_prompt = None
    mock_response = MagicMock()
    mock_response.data = [mock_img]
    mock_openai.images.generate.return_value = mock_response
    mock_openai.images.edit.return_value = mock_response
    client.client = mock_openai
    return client, mock_openai


class TestGenerateImageParams:
    """Verify generate_image builds correct params per model."""

    @pytest.mark.parametrize("model", GPT_IMAGE_MODELS)
    def test_gpt_image_models_omit_response_format(self, model):
        client, mock = _make_client_with_mock()
        client.generate_image(prompt="a cat", model=model, size="1024x1024")
        params = mock.images.generate.call_args[1]
        assert "response_format" not in params, (
            f"response_format must not be sent for {model}"
        )

    @pytest.mark.parametrize("model", DALLE_MODELS)
    def test_dalle_models_include_response_format(self, model):
        client, mock = _make_client_with_mock()
        client.generate_image(prompt="a cat", model=model, size="1024x1024")
        params = mock.images.generate.call_args[1]
        assert params.get("response_format") == "b64_json", (
            f"response_format must be b64_json for {model}"
        )


class TestEditImageParams:
    """Verify edit_image builds correct params per model."""

    @pytest.mark.parametrize("model", GPT_IMAGE_MODELS)
    def test_gpt_image_models_omit_response_format(self, model):
        client, mock = _make_client_with_mock()
        client.edit_image(image_data=b"fakepng", prompt="make it blue", model=model)
        params = mock.images.edit.call_args[1]
        assert "response_format" not in params, (
            f"response_format must not be sent for {model}"
        )
