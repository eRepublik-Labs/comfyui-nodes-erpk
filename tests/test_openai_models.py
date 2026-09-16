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
        """Default model is the current flagship — gpt-5.6-sol."""
        from openai.openai_api.client import OpenAIClient
        assert OpenAIClient.DEFAULT_MODEL == "gpt-5.6-sol"

    def test_gpt_56_tiers_present(self):
        """GPT-5.6 Sol/Terra/Luna are selectable in MODELS."""
        from openai.openai_api.client import OpenAIClient
        for m in ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"):
            assert m in OpenAIClient.MODELS, f"{m} missing from MODELS"

    def test_gpt_56_sol_in_config_sets(self):
        """GPT-5.6 Sol is a gpt-5.x flagship: reasoning + new token param + verbosity."""
        from openai.openai_api.client import OpenAIClient
        assert "gpt-5.6-sol" in OpenAIClient.REASONING_MODELS
        assert "gpt-5.6-sol" in OpenAIClient.NEW_TOKEN_PARAM_MODELS
        assert "gpt-5.6-sol" in OpenAIClient.VERBOSITY_MODELS

    def test_gpt_6_astra_offered_as_reasoning_model(self):
        """gpt-6-astra: Chat Completions supported, reasoning.effort low..max,
        max_completion_tokens family. verbosity is undocumented for it, so it
        must stay out of VERBOSITY_MODELS (omission drops the param; a wrong
        inclusion is a 400 on every non-default selection)."""
        from openai.openai_api.client import OpenAIClient
        assert "gpt-6-astra" in OpenAIClient.MODELS
        assert "gpt-6-astra" in OpenAIClient.REASONING_MODELS
        assert "gpt-6-astra" in OpenAIClient.NEW_TOKEN_PARAM_MODELS
        assert "gpt-6-astra" not in OpenAIClient.VERBOSITY_MODELS
        assert OpenAIClient.DEFAULT_MODEL == "gpt-5.6-sol"


class TestGptImage25:
    """gpt-image-2.5-sunburst / -flare: images/generations + edits only, same
    size envelope as gpt-image-2, quality adds xhigh and max."""

    MODELS_25 = ("gpt-image-2.5-sunburst", "gpt-image-2.5-flare")

    def test_offered_in_image_and_gpt_image_sets(self):
        for m in self.MODELS_25:
            assert m in OpenAIClient.IMAGE_MODELS
            assert m in OpenAIClient.GPT_IMAGE_MODELS
            assert m in OpenAIClient.GPT_IMAGE_2_MODELS

    def test_not_offered_inside_responses_image_tool(self):
        # The model pages list the Responses API as "Not supported".
        from openai.image_nodes import RESPONSES_IMAGE_MODELS
        for m in self.MODELS_25:
            assert m not in RESPONSES_IMAGE_MODELS

    def test_xhigh_and_max_quality_only_reach_25_models(self):
        # "Earlier GPT Image models support quality settings up to high."
        for m in self.MODELS_25:
            assert OpenAIClient._quality_for(m, "max") == "max"
            assert OpenAIClient._quality_for(m, "xhigh") == "xhigh"
        assert OpenAIClient._quality_for("gpt-image-2", "max") == "high"
        assert OpenAIClient._quality_for("gpt-image-2", "xhigh") == "high"
        assert OpenAIClient._quality_for("gpt-image-2", "low") == "low"

