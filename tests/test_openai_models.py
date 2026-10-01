# ABOUTME: Tests for OpenAI model list completeness and configuration sets
# ABOUTME: Verifies reasoning models, token param models, and vision models are consistent

import pytest

from openai.openai_api.client import OpenAIClient


class TestOpenAIModels:
    """Test OpenAI model list and configuration."""

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

    def test_default_model_is_gpt_6_1_sol(self):
        """Alex's call (2026-10-01): gpt-6.1-sol is the default text model."""
        from openai.openai_api.client import OpenAIClient
        assert OpenAIClient.DEFAULT_MODEL == "gpt-6.1-sol"

    def test_every_text_node_defaults_to_gpt_6_1_sol(self):
        from openai.nodes import OpenAITextGeneration, OpenAIChat, OpenAIVision
        for node in (OpenAITextGeneration, OpenAIChat, OpenAIVision):
            model = next(i for i in node.define_schema().inputs if i.id == "model")
            assert model.default == "gpt-6.1-sol", node.__name__
            assert model.default in model.options, node.__name__

    def test_gpt_6_1_sol_offered_as_reasoning_model(self):
        """gpt-6.1-sol, measured on chat.completions 2026-10-01: effort
        low/medium/high/xhigh 200, none/minimal/max 400; verbosity 200;
        legacy max_tokens 400 (needs max_completion_tokens)."""
        from openai.openai_api.client import OpenAIClient
        m = "gpt-6.1-sol"
        assert m in OpenAIClient.MODELS
        assert m in OpenAIClient.REASONING_MODELS
        assert m in OpenAIClient.NEW_TOKEN_PARAM_MODELS
        assert m in OpenAIClient.VERBOSITY_MODELS
        assert OpenAIClient._effort_for(m, "minimal") == "low"
        assert OpenAIClient._effort_for(m, "none") == "low"
        assert OpenAIClient._effort_for(m, "xhigh") == "xhigh"

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
        """gpt-6-astra: Chat Completions supported, reasoning.effort
        low/medium/high/xhigh, max_completion_tokens family. verbosity=low
        returned 200 on chat.completions (measured 2026-09-23), so the
        node's verbosity choice must reach it rather than being dropped."""
        from openai.openai_api.client import OpenAIClient
        assert "gpt-6-astra" in OpenAIClient.MODELS
        assert "gpt-6-astra" in OpenAIClient.REASONING_MODELS
        assert "gpt-6-astra" in OpenAIClient.NEW_TOKEN_PARAM_MODELS
        assert "gpt-6-astra" in OpenAIClient.VERBOSITY_MODELS

    def test_gpt_6_sol_and_luna_offered_as_reasoning_models(self):
        """gpt-6-sol / gpt-6-luna, measured on chat.completions 2026-09-23:
        reasoning_effort none/low/medium/high/xhigh accepted, verbosity=low
        accepted, temperature=0.7 rejected (reasoning models omit it)."""
        from openai.openai_api.client import OpenAIClient
        for m in ("gpt-6-sol", "gpt-6-luna"):
            assert m in OpenAIClient.MODELS, m
            assert m in OpenAIClient.REASONING_MODELS, m
            assert m in OpenAIClient.NEW_TOKEN_PARAM_MODELS, m
            assert m in OpenAIClient.VERBOSITY_MODELS, m


class TestGptImage25:
    """gpt-image-2.5-sunburst / -flare: images/generations + edits only, same
    size envelope as gpt-image-2, quality adds xhigh and max."""

    MODELS_25 = ("gpt-image-2.5-sunburst", "gpt-image-2.5-flare")

    def test_offered_in_image_and_gpt_image_sets(self):
        for m in self.MODELS_25:
            assert m in OpenAIClient.IMAGE_MODELS
            assert m in OpenAIClient.GPT_IMAGE_MODELS
            assert m in OpenAIClient.GPT_IMAGE_2_MODELS

    def test_offered_inside_responses_image_tool(self):
        # The model pages list v1/responses as "Not supported" as a top-level
        # model, but also say: "Select it directly in the Image API or as the
        # model of the Responses API image generation tool." The tool accepted
        # both IDs on 2026-10-01 while rejecting a bogus one.
        from openai.image_nodes import RESPONSES_IMAGE_MODELS
        for m in self.MODELS_25:
            assert m in RESPONSES_IMAGE_MODELS

    def test_xhigh_and_max_quality_only_reach_25_models(self):
        # "Earlier GPT Image models support quality settings up to high."
        for m in self.MODELS_25:
            assert OpenAIClient._quality_for(m, "max") == "max"
            assert OpenAIClient._quality_for(m, "xhigh") == "xhigh"
        assert OpenAIClient._quality_for("gpt-image-2", "max") == "high"
        assert OpenAIClient._quality_for("gpt-image-2", "xhigh") == "high"
        assert OpenAIClient._quality_for("gpt-image-2", "low") == "low"


class TestReasoningEffortClamp:
    """gpt-5.6 Sol/Terra/Luna document none/low/medium/high/xhigh/max and
    gpt-6-astra documents low/medium/high/xhigh/max; neither lists minimal.
    The node offers minimal and none, so unsupported values clamp to low
    rather than earning a 400."""

    def test_minimal_clamps_to_low_on_56_and_6(self):
        for m in ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna",
                  "gpt-6-astra", "gpt-6-sol", "gpt-6-luna"):
            assert OpenAIClient._effort_for(m, "minimal") == "low", m

    def test_none_clamps_only_on_gpt_6(self):
        assert OpenAIClient._effort_for("gpt-6-astra", "none") == "low"
        assert OpenAIClient._effort_for("gpt-5.6-sol", "none") == "none"
        assert OpenAIClient._effort_for("gpt-6-sol", "none") == "none"
        assert OpenAIClient._effort_for("gpt-6-luna", "none") == "none"

    def test_documented_values_pass_through(self):
        assert OpenAIClient._effort_for("gpt-6-astra", "xhigh") == "xhigh"
        assert OpenAIClient._effort_for("gpt-5.6-sol", "low") == "low"



class TestOfferedCatalog:
    """Alex's 2026-10-01 cut: retired and Responses-only text models leave the
    dropdowns (the three -pro models 404 on chat.completions), and the GPT
    Image 1.x models leave the image nodes."""

    KEPT_TEXT = {
        "gpt-6.1-sol", "gpt-6-astra", "gpt-6-sol", "gpt-6-luna",
        "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "chat-latest",
    }
    KEPT_IMAGE = {"gpt-image-2.5-sunburst", "gpt-image-2.5-flare", "gpt-image-2"}

    def test_text_dropdowns_offer_exactly_the_kept_models(self):
        from openai.nodes import TEXT_MODELS, VISION_MODELS
        assert set(TEXT_MODELS) == self.KEPT_TEXT
        assert set(VISION_MODELS) == self.KEPT_TEXT

    def test_per_model_sets_name_only_offered_models(self):
        for name in ("NEW_TOKEN_PARAM_MODELS", "REASONING_MODELS", "VERBOSITY_MODELS"):
            stray = set(getattr(OpenAIClient, name)) - self.KEPT_TEXT
            assert not stray, f"{name} still names {stray}"
        assert set(OpenAIClient.UNSUPPORTED_EFFORT) <= self.KEPT_TEXT

    def test_image_nodes_offer_exactly_the_kept_models(self):
        from openai.image_nodes import IMAGE_MODELS, EDIT_MODELS
        assert set(IMAGE_MODELS) == self.KEPT_IMAGE
        assert set(EDIT_MODELS) == self.KEPT_IMAGE
        assert set(OpenAIClient.GPT_IMAGE_MODELS) == self.KEPT_IMAGE

    def test_generation_quality_drops_dalle_only_values(self):
        # The images reference marks hd and standard "only supported by
        # retired DALL-E models"; no kept model accepts them.
        from openai.image_nodes import OpenAIImageGeneration
        quality = next(i for i in OpenAIImageGeneration.define_schema().inputs if i.id == "quality")
        assert quality.options == ["auto", "low", "medium", "high", "xhigh", "max"]

    def test_every_responses_size_fits_the_gpt_image_2_envelope(self):
        # All kept image models share gpt-image-2's envelope, so a size the
        # preflight rejects (256x256, 512x512) can never succeed.
        from openai.image_nodes import GEN_SIZES
        client = OpenAIClient.__new__(OpenAIClient)
        for size in GEN_SIZES:
            client._validate_size_for_gpt_image_2(size)


class TestMaxTokensCap:
    """gpt-6.1-sol's model page gives 128,000 max output tokens; the node cap
    was 16384, which hid most of that. The default stays at 4096."""

    def test_text_nodes_allow_the_vendor_max_output(self):
        from openai.nodes import OpenAITextGeneration, OpenAIChat, OpenAIVision
        for node in (OpenAITextGeneration, OpenAIChat, OpenAIVision):
            inp = next(i for i in node.define_schema().inputs if i.id == "max_tokens")
            assert inp.max == 128000, node.__name__
            assert inp.default == 4096, node.__name__
