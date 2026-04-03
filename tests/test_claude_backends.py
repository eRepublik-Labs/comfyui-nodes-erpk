# ABOUTME: Tests for Claude enterprise backend clients (Bedrock, Vertex, Foundry).
# ABOUTME: Validates model translation, client construction, and model_override behavior.

"""
Tests for alternate Claude API backends.

Covers:
- Model name translation maps (direct API -> backend-specific IDs)
- model_override precedence over translation
- Client subclass construction with correct SDK args
- send_request model translation
- Eager boto3 check for Bedrock
"""

import sys
import pytest
from unittest.mock import patch, MagicMock

# Import the client classes once at module level to avoid repeated imports
# that trigger numpy reload issues in the test environment.
from claude.claude_api.client import (
    BedrockClaudeClient, VertexClaudeClient, FoundryClaudeClient,
)

# boto3 is not installed in the test environment, so we need to mock it
# for all Bedrock tests. This fixture handles that cleanly.
_mock_boto3 = MagicMock()


def _make_bedrock_client(mock_bedrock_cls, model_override=None, **kwargs):
    """Create a BedrockClaudeClient with mocked boto3 and AnthropicBedrock."""
    mock_bedrock_cls.return_value = MagicMock()
    with patch.dict(sys.modules, {"boto3": _mock_boto3}):
        return BedrockClaudeClient(
            aws_region=kwargs.get("aws_region", "us-east-1"),
            aws_access_key=kwargs.get("aws_access_key"),
            aws_secret_key=kwargs.get("aws_secret_key"),
            model=kwargs.get("model", "claude-sonnet-4-6"),
            model_override=model_override,
        )


def _make_vertex_client(mock_vertex_cls, model_override=None):
    """Create a VertexClaudeClient with mocked AnthropicVertex."""
    mock_vertex_cls.return_value = MagicMock()
    return VertexClaudeClient(
        project_id="test-project",
        region="us-east5",
        model_override=model_override,
    )


def _make_foundry_client(mock_foundry_cls, model_override=None, **kwargs):
    """Create a FoundryClaudeClient with mocked AnthropicFoundry."""
    mock_foundry_cls.return_value = MagicMock()
    return FoundryClaudeClient(
        resource=kwargs.get("resource", "my-resource"),
        api_key=kwargs.get("api_key"),
        model_override=model_override,
    )


# ---------------------------------------------------------------------------
# Bedrock model translation
# ---------------------------------------------------------------------------

class TestBedrockModelTranslation:
    """BedrockClaudeClient translates direct API model names to Bedrock IDs."""

    @patch("anthropic.AnthropicBedrock")
    def test_translates_sonnet_4_6(self, mock_cls):
        client = _make_bedrock_client(mock_cls)
        assert client._translate_model("claude-sonnet-4-6") == "anthropic.claude-sonnet-4-6"

    @patch("anthropic.AnthropicBedrock")
    def test_translates_opus_4_6(self, mock_cls):
        client = _make_bedrock_client(mock_cls)
        assert client._translate_model("claude-opus-4-6") == "anthropic.claude-opus-4-6-v1"

    @patch("anthropic.AnthropicBedrock")
    def test_translates_sonnet_4_5(self, mock_cls):
        client = _make_bedrock_client(mock_cls)
        assert client._translate_model("claude-sonnet-4-5-20250929") == "anthropic.claude-sonnet-4-5-20250929-v1:0"

    @patch("anthropic.AnthropicBedrock")
    def test_translates_haiku_4_5(self, mock_cls):
        client = _make_bedrock_client(mock_cls)
        assert client._translate_model("claude-haiku-4-5-20251001") == "anthropic.claude-haiku-4-5-20251001-v1:0"

    @patch("anthropic.AnthropicBedrock")
    def test_unknown_model_passes_through(self, mock_cls):
        client = _make_bedrock_client(mock_cls)
        assert client._translate_model("claude-future-model") == "claude-future-model"

    @patch("anthropic.AnthropicBedrock")
    def test_model_override_takes_precedence(self, mock_cls):
        client = _make_bedrock_client(mock_cls, model_override="custom-arn:something")
        assert client._translate_model("claude-sonnet-4-6") == "custom-arn:something"


# ---------------------------------------------------------------------------
# Vertex model translation
# ---------------------------------------------------------------------------

class TestVertexModelTranslation:
    """VertexClaudeClient translates direct API model names to Vertex IDs."""

    @patch("anthropic.AnthropicVertex")
    def test_sonnet_4_6_unchanged(self, mock_cls):
        client = _make_vertex_client(mock_cls)
        assert client._translate_model("claude-sonnet-4-6") == "claude-sonnet-4-6"

    @patch("anthropic.AnthropicVertex")
    def test_opus_4_6_unchanged(self, mock_cls):
        client = _make_vertex_client(mock_cls)
        assert client._translate_model("claude-opus-4-6") == "claude-opus-4-6"

    @patch("anthropic.AnthropicVertex")
    def test_translates_sonnet_4_5(self, mock_cls):
        client = _make_vertex_client(mock_cls)
        assert client._translate_model("claude-sonnet-4-5-20250929") == "claude-sonnet-4-5@20250929"

    @patch("anthropic.AnthropicVertex")
    def test_translates_haiku_4_5(self, mock_cls):
        client = _make_vertex_client(mock_cls)
        assert client._translate_model("claude-haiku-4-5-20251001") == "claude-haiku-4-5@20251001"

    @patch("anthropic.AnthropicVertex")
    def test_unknown_model_passes_through(self, mock_cls):
        client = _make_vertex_client(mock_cls)
        assert client._translate_model("claude-future-model") == "claude-future-model"

    @patch("anthropic.AnthropicVertex")
    def test_model_override_takes_precedence(self, mock_cls):
        client = _make_vertex_client(mock_cls, model_override="claude-sonnet-4-5@custom")
        assert client._translate_model("claude-sonnet-4-6") == "claude-sonnet-4-5@custom"


# ---------------------------------------------------------------------------
# Foundry model translation
# ---------------------------------------------------------------------------

class TestFoundryModelTranslation:
    """FoundryClaudeClient passes model names through (no translation needed)."""

    @patch("anthropic.AnthropicFoundry")
    def test_sonnet_4_6_unchanged(self, mock_cls):
        client = _make_foundry_client(mock_cls)
        assert client._translate_model("claude-sonnet-4-6") == "claude-sonnet-4-6"

    @patch("anthropic.AnthropicFoundry")
    def test_model_override_takes_precedence(self, mock_cls):
        client = _make_foundry_client(mock_cls, model_override="my-deployment")
        assert client._translate_model("claude-sonnet-4-6") == "my-deployment"


# ---------------------------------------------------------------------------
# Client construction
# ---------------------------------------------------------------------------

class TestBedrockClientConstruction:
    """BedrockClaudeClient passes correct args to AnthropicBedrock."""

    @patch("anthropic.AnthropicBedrock")
    def test_passes_region(self, mock_cls):
        _make_bedrock_client(mock_cls, aws_region="eu-west-1")
        mock_cls.assert_called_once()
        assert mock_cls.call_args[1]["aws_region"] == "eu-west-1"

    @patch("anthropic.AnthropicBedrock")
    def test_passes_credentials(self, mock_cls):
        _make_bedrock_client(mock_cls, aws_access_key="AKIA...", aws_secret_key="secret")
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["aws_access_key"] == "AKIA..."
        assert call_kwargs["aws_secret_key"] == "secret"

    @patch("anthropic.AnthropicBedrock")
    def test_omits_none_credentials(self, mock_cls):
        _make_bedrock_client(mock_cls)
        call_kwargs = mock_cls.call_args[1]
        assert "aws_access_key" not in call_kwargs
        assert "aws_secret_key" not in call_kwargs

    @patch("anthropic.AnthropicBedrock")
    def test_sets_model(self, mock_cls):
        client = _make_bedrock_client(mock_cls, model="claude-opus-4-6")
        assert client.model == "claude-opus-4-6"

    @patch("anthropic.AnthropicBedrock")
    def test_initializes_usage_tracking(self, mock_cls):
        client = _make_bedrock_client(mock_cls)
        assert client.total_input_tokens == 0
        assert client.total_output_tokens == 0


class TestVertexClientConstruction:
    """VertexClaudeClient passes correct args to AnthropicVertex."""

    @patch("anthropic.AnthropicVertex")
    def test_passes_project_and_region(self, mock_cls):
        mock_cls.return_value = MagicMock()
        VertexClaudeClient(project_id="my-project", region="europe-west1")
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["project_id"] == "my-project"
        assert call_kwargs["region"] == "europe-west1"


class TestFoundryClientConstruction:
    """FoundryClaudeClient passes correct args to AnthropicFoundry."""

    @patch("anthropic.AnthropicFoundry")
    def test_passes_resource(self, mock_cls):
        _make_foundry_client(mock_cls, resource="my-resource")
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["resource"] == "my-resource"

    @patch("anthropic.AnthropicFoundry")
    def test_passes_api_key(self, mock_cls):
        _make_foundry_client(mock_cls, api_key="test-key")
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["api_key"] == "test-key"

    @patch("anthropic.AnthropicFoundry")
    def test_omits_none_api_key(self, mock_cls):
        _make_foundry_client(mock_cls)
        call_kwargs = mock_cls.call_args[1]
        assert "api_key" not in call_kwargs


# ---------------------------------------------------------------------------
# send_request model translation
# ---------------------------------------------------------------------------

class TestBedrockSendRequestTranslation:
    """send_request translates model before calling the SDK."""

    @patch("anthropic.AnthropicBedrock")
    def test_send_request_translates_model(self, mock_cls):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        mock_response.usage.cache_read_input_tokens = 0
        mock_response.usage.cache_creation_input_tokens = 0
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client

        client = _make_bedrock_client(mock_cls, model="claude-sonnet-4-6")
        client.client = mock_client  # Replace with our pre-configured mock
        client.send_request(messages=[{"role": "user", "content": "hi"}])

        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "anthropic.claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# Bedrock boto3 early check
# ---------------------------------------------------------------------------

class TestBedrockBoto3Check:
    """BedrockClaudeClient checks for boto3 at construction time."""

    @patch("anthropic.AnthropicBedrock")
    def test_raises_import_error_without_boto3(self, mock_cls):
        with patch.dict(sys.modules, {"boto3": None}):
            with pytest.raises(ImportError, match="boto3"):
                BedrockClaudeClient(aws_region="us-east-1")
