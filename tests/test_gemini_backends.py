# ABOUTME: Tests for Gemini Vertex AI backend client.
# ABOUTME: Validates VertexGeminiClient construction and model_override behavior.

"""
Tests for Gemini Vertex AI backend.

Covers:
- VertexGeminiClient is a subclass of GeminiClient
- model_override takes precedence
- No model translation needed (Vertex uses same IDs)
"""

import pytest
from unittest.mock import patch, MagicMock

from gemini.gemini_api.client import GeminiClient, VertexGeminiClient


class TestVertexGeminiClientExists:
    """VertexGeminiClient can be imported and is a subclass."""

    def test_is_subclass_of_gemini_client(self):
        assert issubclass(VertexGeminiClient, GeminiClient)


class TestVertexGeminiModelOverride:
    """model_override takes precedence in _translate_model."""

    @patch("google.genai.Client")
    def test_model_passes_through_unchanged(self, mock_client_cls):
        mock_client_cls.return_value = MagicMock()
        client = VertexGeminiClient(project="test-project")
        assert client._translate_model("gemini-2.5-flash") == "gemini-2.5-flash"

    @patch("google.genai.Client")
    def test_model_override_takes_precedence(self, mock_client_cls):
        mock_client_cls.return_value = MagicMock()
        client = VertexGeminiClient(project="test-project", model_override="custom-model")
        assert client._translate_model("gemini-2.5-flash") == "custom-model"


class TestVertexGeminiClientConstruction:
    """VertexGeminiClient passes correct args to genai.Client."""

    @patch("google.genai.Client")
    def test_passes_vertexai_true(self, mock_client_cls):
        mock_client_cls.return_value = MagicMock()
        VertexGeminiClient(project="my-project", location="europe-west4")
        call_kwargs = mock_client_cls.call_args[1]
        assert call_kwargs["vertexai"] is True
        assert call_kwargs["project"] == "my-project"
        assert call_kwargs["location"] == "europe-west4"

    @patch("google.genai.Client")
    def test_does_not_pass_api_key(self, mock_client_cls):
        mock_client_cls.return_value = MagicMock()
        VertexGeminiClient(project="my-project")
        call_kwargs = mock_client_cls.call_args[1]
        assert "api_key" not in call_kwargs

    @patch("google.genai.Client")
    def test_initializes_config_state(self, mock_client_cls):
        mock_client_cls.return_value = MagicMock()
        client = VertexGeminiClient(project="my-project")
        assert client.system_instruction is None
        assert client.safety_settings is None
