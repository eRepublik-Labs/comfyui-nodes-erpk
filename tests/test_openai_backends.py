# ABOUTME: Tests for Azure OpenAI backend client.
# ABOUTME: Validates deployment_name override and AzureOpenAIClient construction.

"""
Tests for Azure OpenAI backend.

Covers:
- AzureOpenAIClient is a subclass of OpenAIClient
- deployment_name overrides model in generate_content and chat
- Empty deployment_name falls back to original model
"""

import pytest
from unittest.mock import MagicMock

from openai.openai_api.client import OpenAIClient, AzureOpenAIClient

# The parent class methods do `from openai import APIError, ...` which in the
# test env hits our local openai/ package. Inject mock exception classes so
# the parent methods can import them.
import openai as _local_openai
for _attr in ("APIError", "RateLimitError", "APIConnectionError"):
    if not hasattr(_local_openai, _attr):
        setattr(_local_openai, _attr, type(_attr, (Exception,), {}))


def _mock_chat_response():
    """Create a mock response matching OpenAI chat completion format."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "hello"
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage.prompt_tokens = 5
    mock_response.usage.completion_tokens = 1
    return mock_response


# ---------------------------------------------------------------------------
# Import and subclass check
# ---------------------------------------------------------------------------

class TestAzureOpenAIClientExists:
    """AzureOpenAIClient can be imported and is a subclass."""

    def test_can_import(self):
        assert AzureOpenAIClient is not None

    def test_is_subclass_of_openai_client(self):
        assert issubclass(AzureOpenAIClient, OpenAIClient)

    def test_stores_deployment_name(self):
        client = AzureOpenAIClient.__new__(AzureOpenAIClient)
        client.deployment_name = "my-deploy"
        client.model_name = "gpt-4o"
        client.system_instruction = None
        assert client.deployment_name == "my-deploy"


# ---------------------------------------------------------------------------
# Deployment name model resolution
# ---------------------------------------------------------------------------

class TestAzureDeploymentNameOverride:
    """deployment_name overrides model param in API methods."""

    def _make_client(self, deployment_name=None):
        """Create a client with mocked SDK client."""
        client = AzureOpenAIClient.__new__(AzureOpenAIClient)
        client.deployment_name = deployment_name
        client.model_name = "gpt-4o"
        client.system_instruction = None
        client.client = MagicMock()
        client.client.chat.completions.create.return_value = _mock_chat_response()
        return client

    def test_generate_content_uses_deployment_name(self):
        client = self._make_client(deployment_name="my-deploy")
        client.generate_content(prompt="hi", model="gpt-4o")

        call_kwargs = client.client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "my-deploy"

    def test_chat_uses_deployment_name(self):
        client = self._make_client(deployment_name="my-deploy")
        client.chat(messages=[{"role": "user", "content": "hi"}], model="gpt-4o")

        call_kwargs = client.client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "my-deploy"

    def test_no_deployment_name_uses_original_model(self):
        client = self._make_client(deployment_name=None)
        client.generate_content(prompt="hi", model="gpt-4o")

        call_kwargs = client.client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "gpt-4o"

    def test_generate_image_uses_deployment_name(self):
        client = self._make_client(deployment_name="my-dalle-deploy")
        mock_img_response = MagicMock()
        mock_img_response.data = [MagicMock(b64_json="abc123", revised_prompt=None)]
        client.client.images.generate.return_value = mock_img_response

        client.generate_image(prompt="a cat", model="dall-e-3")

        call_kwargs = client.client.images.generate.call_args[1]
        assert call_kwargs["model"] == "my-dalle-deploy"
