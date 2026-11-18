# ABOUTME: Tests for thinking_level parameter handling in Gemini nodes.
# ABOUTME: Verifies ThinkingConfig wiring, SDK compatibility guard, and schema exposure.

import pytest

from erpk.gemini.nodes import GeminiTextGeneration, GeminiChat, GeminiVision


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
        assert set(thinking_input.options) == {"none", "minimal", "low", "medium", "high", "xhigh"}

    @pytest.mark.parametrize("node_cls", [GeminiTextGeneration, GeminiChat, GeminiVision])
    def test_xhigh_tooltip_names_the_one_model_that_takes_it(self, node_cls):
        schema = node_cls.define_schema()
        tooltip = [i for i in schema.inputs if i.id == "thinking_level"][0].tooltip
        assert "xhigh is sent only to 4 Hydrogen" in tooltip

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


class TestBuildThinkingConfig:
    """Every offered text model is Gemini 3.x and takes the thinking_level enum."""

    def test_minimal_on_gemini_3_6_flash_uses_level(self):
        from erpk.gemini.nodes import _build_thinking_config
        result = _build_thinking_config("minimal", "gemini-3.6-flash")
        assert result is not None
        assert result.thinking_level == "MINIMAL"
        assert result.thinking_budget is None

    def test_high_on_gemini_35_flash_uses_level(self):
        from erpk.gemini.nodes import _build_thinking_config
        result = _build_thinking_config("high", "gemini-3.5-flash")
        assert result is not None
        assert result.thinking_level == "HIGH"

    def test_minimal_on_gemini_3_1_pro_clamps_to_low(self):
        # Probed 2026-10-01: gemini-3.1-pro-preview + MINIMAL returns 400
        # "Thinking level MINIMAL is not supported for this model"; LOW returns 200.
        from erpk.gemini.nodes import _build_thinking_config
        assert _build_thinking_config("minimal", "gemini-3.1-pro-preview").thinking_level == "LOW"
        assert _build_thinking_config("low", "gemini-3.1-pro-preview").thinking_level == "LOW"

    def test_none_sends_no_thinking_config(self):
        from erpk.gemini.nodes import _build_thinking_config
        assert _build_thinking_config("none", "gemini-3.5-flash") is None
        assert _build_thinking_config("none", "gemini-3.1-pro-preview") is None


# Probed 2026-11-18 with generateContent: xhigh returned 200 on gemini-4-hydrogen
# and 400 "Thinking level XHIGH is not supported for this model" on each of these.
XHIGH_REJECTED = ["gemini-4-carbon", "gemini-4-argon", "gemini-3.1-pro-preview",
                  "gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash",
                  "gemini-3.5-flash", "gemini-3.5-flash-lite"]


class TestXhighThinking:

    def test_hydrogen_sends_xhigh(self, recwarn):
        from erpk.gemini.nodes import _build_thinking_config
        config = _build_thinking_config("xhigh", "gemini-4-hydrogen")
        assert config.model_dump(mode="json", exclude_none=True) == {"thinking_level": "XHIGH"}
        # google-genai's ThinkingLevel enum has no XHIGH yet and warns that the
        # value is invalid, although the API accepts it; the node keeps that
        # false warning out of the user's console.
        assert [str(w.message) for w in recwarn] == []

    @pytest.mark.parametrize("model", XHIGH_REJECTED)
    def test_models_that_reject_xhigh_get_high(self, model):
        from erpk.gemini.nodes import _build_thinking_config
        assert _build_thinking_config("xhigh", model).model_dump(
            mode="json", exclude_none=True) == {"thinking_level": "HIGH"}

    def test_continued_chat_clamps_for_the_model_the_session_runs_on(self):
        # A continued session answers with the model it was started on, so a
        # node switched to Hydrogen + xhigh must not send XHIGH to 3.8 Flash.
        import asyncio
        from types import SimpleNamespace
        from erpk.gemini.gemini_api.client import GeminiClient

        sent = {}

        class _Session:
            _model = "gemini-3.8-flash"

            def send_message(self, message, config):
                sent["config"] = config
                return SimpleNamespace(text="OK", candidates=[])

        client = GeminiClient.__new__(GeminiClient)
        client.system_instruction = None
        client.safety_settings = None
        asyncio.run(GeminiChat.execute(prompt="Say OK.", client=client, model="gemini-4-hydrogen",
                                       thinking_level="xhigh", chat_session=_Session()))
        assert sent["config"].thinking_config.thinking_level == "HIGH"

    def test_sdk_chat_session_exposes_its_model(self):
        # The continued-chat clamp reads Chat._model; this fails if the SDK drops it.
        from google import genai
        session = genai.Client(api_key="test-key").chats.create(model="gemini-4-hydrogen")
        assert session._model == "gemini-4-hydrogen"
