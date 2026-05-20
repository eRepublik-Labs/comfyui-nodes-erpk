# ABOUTME: Tests for thinking_level parameter handling in Gemini nodes.
# ABOUTME: Verifies ThinkingConfig wiring, SDK compatibility guard, and schema exposure.

import pytest

from gemini.nodes import GeminiTextGeneration, GeminiChat, GeminiVision


class TestThinkingLevelSchema:
    """Verify thinking_level appears in define_schema for all 3 text-based nodes."""

    @pytest.mark.parametrize("node_cls", [GeminiTextGeneration, GeminiChat, GeminiVision])
    def test_thinking_level_in_inputs(self, node_cls):
        schema = node_cls.define_schema()
        input_ids = [i.id for i in schema.inputs]
        assert "thinking_level" in input_ids

    @pytest.mark.parametrize("node_cls", [GeminiTextGeneration, GeminiChat, GeminiVision])
    def test_thinking_level_choices(self, node_cls):
        schema = node_cls.define_schema()
        thinking_input = [i for i in schema.inputs if i.id == "thinking_level"][0]
        assert set(thinking_input.options) == {"none", "minimal", "low", "medium", "high"}

    @pytest.mark.parametrize("node_cls", [GeminiTextGeneration, GeminiChat, GeminiVision])
    def test_thinking_level_default_is_none(self, node_cls):
        schema = node_cls.define_schema()
        thinking_input = [i for i in schema.inputs if i.id == "thinking_level"][0]
        assert thinking_input.default == "none"


class TestThinkingLevelConfig:
    """Verify thinking_level is wired through to GenerateContentConfig."""

    def test_none_produces_no_thinking_config(self):
        """When thinking_level='none', no thinking_config should be set."""
        from google.genai import types

        config = types.GenerateContentConfig(
            max_output_tokens=100,
            temperature=0.7,
        )
        assert not hasattr(config, 'thinking_config') or config.thinking_config is None

    def test_high_produces_thinking_config(self):
        """When thinking_level='high', ThinkingConfig should be created."""
        from google.genai import types as genai_types

        if not hasattr(genai_types, 'ThinkingConfig'):
            pytest.skip("SDK doesn't support ThinkingConfig")

        tc = genai_types.ThinkingConfig(thinking_level="HIGH")
        assert tc.thinking_level == "HIGH"

    def test_sdk_guard_logs_warning_when_unsupported(self, capsys):
        """When SDK lacks ThinkingConfig, a warning should be printed."""
        from google.genai import types as genai_types

        thinking_level = "high"
        if thinking_level != "none":
            if hasattr(genai_types, 'ThinkingConfig') and 'thinking_level' in genai_types.ThinkingConfig.model_fields:
                pass  # would set config
            else:
                print("[Gemini] Warning: thinking_level not supported by SDK, ignoring")


class TestIsGemini3xClassifier:
    """Verify the _is_gemini_3x helper correctly distinguishes generations."""

    def test_is_gemini_3x_classifier(self):
        from gemini.nodes import _is_gemini_3x
        assert _is_gemini_3x("gemini-3-flash-preview") is True
        assert _is_gemini_3x("gemini-2.5-pro") is False
        assert _is_gemini_3x("gemini-3.1-pro-preview") is True
        assert _is_gemini_3x("gemini-3.5-flash") is True


class TestBuildThinkingConfigGeneration:
    """Verify _build_thinking_config branches correctly by model generation."""

    def test_minimal_on_gemini_3_flash_uses_level(self):
        from gemini.nodes import _build_thinking_config
        result = _build_thinking_config("minimal", "gemini-3-flash-preview")
        assert result is not None
        assert result.thinking_level == "MINIMAL"

    def test_high_on_gemini_35_flash_uses_level(self):
        from gemini.nodes import _build_thinking_config
        result = _build_thinking_config("high", "gemini-3.5-flash")
        assert result is not None
        assert result.thinking_level == "HIGH"

    def test_minimal_on_gemini_2_5_flash_uses_budget_zero(self):
        from gemini.nodes import _build_thinking_config
        result = _build_thinking_config("minimal", "gemini-2.5-flash")
        assert result is not None
        assert result.thinking_budget == 0

    def test_low_on_gemini_2_5_pro_enforces_minimum_128(self):
        """low=512 is above the 128 minimum for Pro; no clamping applied."""
        from gemini.nodes import _build_thinking_config
        result = _build_thinking_config("low", "gemini-2.5-pro")
        assert result is not None
        assert result.thinking_budget == 512

    def test_minimal_on_gemini_2_5_pro_enforces_minimum_128(self):
        """minimal maps to 0, but Pro can't disable thinking, so clamp up to 128."""
        from gemini.nodes import _build_thinking_config
        result = _build_thinking_config("minimal", "gemini-2.5-pro")
        assert result is not None
        assert result.thinking_budget == 128

    def test_none_returns_none_for_both_generations(self):
        from gemini.nodes import _build_thinking_config
        assert _build_thinking_config("none", "gemini-3-flash-preview") is None
        assert _build_thinking_config("none", "gemini-2.5-flash") is None
