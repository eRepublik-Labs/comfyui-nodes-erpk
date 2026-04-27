# ABOUTME: Tests for OpenAI model list completeness and configuration sets
# ABOUTME: Verifies reasoning models, token param models, and vision models are consistent

import pytest

from openai.openai_api.client import OpenAIClient


class TestOpenAIModels:
    """Test OpenAI model list and configuration."""

    def test_o3_mini_in_models(self):
        """o3-mini should be in the MODELS dict."""
        from openai.openai_api.client import OpenAIClient
        assert "o3-mini" in OpenAIClient.MODELS

    def test_o3_pro_in_models(self):
        """o3-pro should be in the MODELS dict."""
        from openai.openai_api.client import OpenAIClient
        assert "o3-pro" in OpenAIClient.MODELS

    def test_o3_mini_in_reasoning_models(self):
        """o3-mini is a reasoning model — no temperature/top_p/stop."""
        from openai.openai_api.client import OpenAIClient
        assert "o3-mini" in OpenAIClient.REASONING_MODELS

    def test_o3_pro_in_reasoning_models(self):
        """o3-pro is a reasoning model — no temperature/top_p/stop."""
        from openai.openai_api.client import OpenAIClient
        assert "o3-pro" in OpenAIClient.REASONING_MODELS

    def test_o3_mini_in_new_token_param_models(self):
        """o3-mini uses max_completion_tokens instead of max_tokens."""
        from openai.openai_api.client import OpenAIClient
        assert "o3-mini" in OpenAIClient.NEW_TOKEN_PARAM_MODELS

    def test_o3_pro_in_new_token_param_models(self):
        """o3-pro uses max_completion_tokens instead of max_tokens."""
        from openai.openai_api.client import OpenAIClient
        assert "o3-pro" in OpenAIClient.NEW_TOKEN_PARAM_MODELS

    def test_all_reasoning_models_in_new_token_param(self):
        """Every reasoning model should also use max_completion_tokens."""
        from openai.openai_api.client import OpenAIClient
        for model in OpenAIClient.REASONING_MODELS:
            assert model in OpenAIClient.NEW_TOKEN_PARAM_MODELS, (
                f"{model} is in REASONING_MODELS but not NEW_TOKEN_PARAM_MODELS"
            )

    def test_all_reasoning_models_in_models_dict(self):
        """Every reasoning model should appear in the main MODELS dict."""
        from openai.openai_api.client import OpenAIClient
        for model in OpenAIClient.REASONING_MODELS:
            assert model in OpenAIClient.MODELS, (
                f"{model} is in REASONING_MODELS but not MODELS"
            )

    def test_existing_models_still_present(self):
        """Sanity check: existing models should not be removed."""
        from openai.openai_api.client import OpenAIClient
        expected = ["gpt-5.2", "gpt-5.2-pro", "gpt-5.1", "gpt-5",
                     "gpt-5-mini", "gpt-5-nano", "gpt-4.1", "gpt-4.1-mini",
                     "gpt-4.1-nano", "gpt-4o", "gpt-4o-mini", "o4-mini", "o3"]
        for model in expected:
            assert model in OpenAIClient.MODELS, f"Missing model: {model}"

    def test_default_model_is_current_flagship(self):
        """Default model is the premium flagship — gpt-5.5."""
        from openai.openai_api.client import OpenAIClient
        assert OpenAIClient.DEFAULT_MODEL == "gpt-5.5"
