# ABOUTME: Tests for OpenAI reasoning_effort parameter and gpt-5.4 family models
# ABOUTME: Validates schema inputs, SDK pass-through for reasoning models, and drop for non-reasoning

import asyncio
import importlib
from unittest.mock import MagicMock

import pytest

IO = pytest.importorskip("comfy_api.latest").IO

# In the test environment, our local openai/ package shadows the SDK's openai package.
# The client does `from openai import APIError, RateLimitError, APIConnectionError`
# (lazy import inside methods) — inject stubs so the import resolves.
import openai as _local_openai
for _name in ("APIError", "RateLimitError", "APIConnectionError"):
    if not hasattr(_local_openai, _name):
        setattr(_local_openai, _name, type(_name, (Exception,), {}))

from openai.openai_api.client import OpenAIClient


REASONING_EFFORT_OPTIONS = ["none", "minimal", "low", "medium", "high", "xhigh"]
VERBOSITY_OPTIONS = ["default", "low", "medium", "high"]


def _import_node(module_name, class_name):
    """Import a node class from the openai package."""
    mod = importlib.import_module(f"openai.{module_name}")
    return getattr(mod, class_name)


class TestGPT54FamilyInModels:
    """gpt-5.4 family is present in OpenAIClient.MODELS and related sets."""

    @pytest.mark.parametrize("model_id", [
        "gpt-5.4", "gpt-5.4-pro", "gpt-5.4-mini", "gpt-5.4-nano",
    ])
    def test_gpt_5_4_family_in_models(self, model_id):
        assert model_id in OpenAIClient.MODELS, (
            f"{model_id} must be present in OpenAIClient.MODELS"
        )

    @pytest.mark.parametrize("model_id", [
        "gpt-5.4", "gpt-5.4-pro", "gpt-5.4-mini", "gpt-5.4-nano",
    ])
    def test_gpt_5_4_family_uses_max_completion_tokens(self, model_id):
        assert model_id in OpenAIClient.NEW_TOKEN_PARAM_MODELS, (
            f"{model_id} should use max_completion_tokens"
        )

    @pytest.mark.parametrize("model_id", [
        "gpt-5.4", "gpt-5.4-pro", "gpt-5.4-mini", "gpt-5.4-nano",
    ])
    def test_gpt_5_4_family_supports_reasoning(self, model_id):
        assert model_id in OpenAIClient.REASONING_MODELS, (
            f"{model_id} should support reasoning_effort"
        )


class TestGPT55FamilyInModels:
    """gpt-5.5 family (gpt-5.5 + gpt-5.5-pro) is wired into all relevant sets.

    Released 2026-04-23. The base gpt-5.5 is the premium flagship; gpt-5.5-pro
    is an extended-compute Responses API variant at $30/$180 per MTok with no
    streaming support. Both use max_completion_tokens and support reasoning_effort.
    """

    @pytest.mark.parametrize("model_id", ["gpt-5.5", "gpt-5.5-pro"])
    def test_gpt_5_5_family_in_models(self, model_id):
        assert model_id in OpenAIClient.MODELS, (
            f"{model_id} must be present in OpenAIClient.MODELS"
        )

    @pytest.mark.parametrize("model_id", ["gpt-5.5", "gpt-5.5-pro"])
    def test_gpt_5_5_family_uses_max_completion_tokens(self, model_id):
        assert model_id in OpenAIClient.NEW_TOKEN_PARAM_MODELS, (
            f"{model_id} should use max_completion_tokens like the rest of the gpt-5 family"
        )

    @pytest.mark.parametrize("model_id", ["gpt-5.5", "gpt-5.5-pro"])
    def test_gpt_5_5_family_supports_reasoning(self, model_id):
        assert model_id in OpenAIClient.REASONING_MODELS, (
            f"{model_id} must support reasoning_effort"
        )

    @pytest.mark.parametrize("model_id", ["gpt-5.5", "gpt-5.5-pro"])
    def test_gpt_5_5_family_in_responses_mainline_models(self, model_id):
        from openai.image_nodes import RESPONSES_MAINLINE_MODELS
        assert model_id in RESPONSES_MAINLINE_MODELS, (
            f"{model_id} must be selectable as a mainline model on the Image Responses node"
        )

    def test_gpt_5_5_appears_first_in_dropdown(self):
        """5.5 (base) is the premium flagship — should be first in the model dropdown."""
        from openai.nodes import TEXT_MODELS
        assert TEXT_MODELS[0] == "gpt-5.5", (
            f"gpt-5.5 should be the first option in TEXT_MODELS, got {TEXT_MODELS[0]}"
        )

    def test_gpt_5_5_pro_appears_second_in_dropdown(self):
        """5.5-pro is the premium-of-premium tier — should sit right after 5.5."""
        from openai.nodes import TEXT_MODELS
        assert TEXT_MODELS[1] == "gpt-5.5-pro", (
            f"gpt-5.5-pro should be the second option in TEXT_MODELS, got {TEXT_MODELS[1]}"
        )


class TestVisionModelsDerivedFromModels:
    """VISION_MODELS is derived from MODELS and excludes o-series."""

    def test_vision_models_subset_of_models(self):
        from openai.nodes import VISION_MODELS
        for m in VISION_MODELS:
            assert m in OpenAIClient.MODELS, (
                f"{m} in VISION_MODELS but not in MODELS"
            )

    def test_vision_models_excludes_o_series(self):
        from openai.nodes import VISION_MODELS
        for m in VISION_MODELS:
            assert not m.startswith("o"), (
                f"{m} is an o-series reasoning model and should not be in VISION_MODELS"
            )

    def test_vision_models_includes_all_non_o_models(self):
        """Every non-o model in MODELS should appear in VISION_MODELS."""
        from openai.nodes import VISION_MODELS
        expected = {m for m in OpenAIClient.MODELS if not m.startswith("o")}
        assert set(VISION_MODELS) == expected


class TestReasoningEffortSchema:
    """reasoning_effort appears as an input on text/chat/vision nodes."""

    @pytest.mark.parametrize("module,class_name", [
        ("nodes", "OpenAITextGeneration"),
        ("nodes", "OpenAIChat"),
        ("nodes", "OpenAIVision"),
    ])
    def test_reasoning_effort_in_schema(self, module, class_name):
        cls = _import_node(module, class_name)
        schema = cls.define_schema()
        matches = [i for i in schema.inputs if i.id == "reasoning_effort"]
        assert len(matches) == 1, (
            f"{class_name} must expose exactly one reasoning_effort input"
        )
        inp = matches[0]
        assert inp.optional is True
        assert set(inp.options) == set(REASONING_EFFORT_OPTIONS)
        assert inp.default == "none"

    def test_reasoning_effort_in_text_gen_schema(self):
        cls = _import_node("nodes", "OpenAITextGeneration")
        schema = cls.define_schema()
        ids = [i.id for i in schema.inputs]
        assert "reasoning_effort" in ids

    def test_reasoning_effort_in_chat_schema(self):
        cls = _import_node("nodes", "OpenAIChat")
        schema = cls.define_schema()
        ids = [i.id for i in schema.inputs]
        assert "reasoning_effort" in ids

    def test_reasoning_effort_in_vision_schema(self):
        cls = _import_node("nodes", "OpenAIVision")
        schema = cls.define_schema()
        ids = [i.id for i in schema.inputs]
        assert "reasoning_effort" in ids


class TestVerbositySchema:
    """verbosity appears as an input on text/chat/vision/image-responses nodes."""

    @pytest.mark.parametrize("module,class_name", [
        ("nodes", "OpenAITextGeneration"),
        ("nodes", "OpenAIChat"),
        ("nodes", "OpenAIVision"),
        ("image_nodes", "OpenAIImageResponses"),
    ])
    def test_verbosity_in_schema(self, module, class_name):
        cls = _import_node(module, class_name)
        schema = cls.define_schema()
        matches = [i for i in schema.inputs if i.id == "verbosity"]
        assert len(matches) == 1, (
            f"{class_name} must expose exactly one verbosity input"
        )
        inp = matches[0]
        assert inp.optional is True
        assert set(inp.options) == set(VERBOSITY_OPTIONS)
        assert inp.default == "default"


class TestVerbosityModelsSet:
    """VERBOSITY_MODELS controls which models receive the verbosity param."""

    @pytest.mark.parametrize("model_id", [
        "gpt-5.5", "gpt-5.5-pro",
        "gpt-5.4", "gpt-5.4-pro", "gpt-5.4-mini", "gpt-5.4-nano",
        "gpt-5.2", "gpt-5.2-pro", "gpt-5.1",
        "gpt-5", "gpt-5-mini", "gpt-5-nano",
    ])
    def test_gpt_5_x_in_verbosity_models(self, model_id):
        assert model_id in OpenAIClient.VERBOSITY_MODELS, (
            f"{model_id} should accept the verbosity parameter"
        )

    @pytest.mark.parametrize("model_id", [
        "gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano",
        "o3", "o3-mini", "o3-pro", "o4-mini",
    ])
    def test_non_gpt_5_x_excluded_from_verbosity(self, model_id):
        assert model_id not in OpenAIClient.VERBOSITY_MODELS, (
            f"{model_id} should NOT be in VERBOSITY_MODELS — verbosity is a gpt-5.x parameter"
        )


def _make_client_with_mock_sdk():
    """Build an OpenAIClient instance with the SDK mocked out (no __init__)."""
    client = OpenAIClient.__new__(OpenAIClient)
    client.model_name = "gpt-4o"
    client.system_instruction = None

    mock_sdk = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "ok"
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage.prompt_tokens = 1
    mock_response.usage.completion_tokens = 1
    mock_sdk.chat.completions.create.return_value = mock_response

    client.client = mock_sdk
    return client, mock_sdk


class TestReasoningEffortPassThrough:
    """reasoning_effort is forwarded to SDK only for reasoning models."""

    def test_reasoning_effort_passed_to_sdk_for_reasoning_model(self):
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.generate_content(
            prompt="hello",
            model="gpt-5.4",
            reasoning_effort="high",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert kwargs.get("reasoning_effort") == "high"

    def test_reasoning_effort_dropped_for_non_reasoning_model(self):
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.generate_content(
            prompt="hello",
            model="gpt-4o",
            reasoning_effort="high",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert "reasoning_effort" not in kwargs

    def test_reasoning_effort_passed_for_o3(self):
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.generate_content(
            prompt="hello",
            model="o3",
            reasoning_effort="medium",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert kwargs.get("reasoning_effort") == "medium"

    def test_reasoning_effort_none_not_passed(self):
        """When reasoning_effort is None (default), it is never passed."""
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.generate_content(
            prompt="hello",
            model="gpt-5.4",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert "reasoning_effort" not in kwargs

    def test_reasoning_effort_passed_via_chat(self):
        """chat() should forward reasoning_effort for reasoning models."""
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.chat(
            messages=[{"role": "user", "content": "hi"}],
            model="gpt-5.4-pro",
            reasoning_effort="xhigh",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert kwargs.get("reasoning_effort") == "xhigh"

    def test_reasoning_effort_dropped_via_chat_for_non_reasoning(self):
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.chat(
            messages=[{"role": "user", "content": "hi"}],
            model="gpt-4o",
            reasoning_effort="low",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert "reasoning_effort" not in kwargs


class TestVerbosityPassThrough:
    """verbosity is forwarded only when (a) value != 'default' and (b) model in VERBOSITY_MODELS."""

    def test_verbosity_passed_for_gpt_5_5(self):
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.generate_content(
            prompt="hello",
            model="gpt-5.5",
            verbosity="low",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert kwargs.get("verbosity") == "low"

    def test_verbosity_passed_for_gpt_5_5_pro(self):
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.generate_content(
            prompt="hello",
            model="gpt-5.5-pro",
            verbosity="high",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert kwargs.get("verbosity") == "high"

    def test_verbosity_dropped_when_default(self):
        """'default' is the no-op marker — never sent over the wire."""
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.generate_content(
            prompt="hello",
            model="gpt-5.5",
            verbosity="default",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert "verbosity" not in kwargs

    def test_verbosity_dropped_when_omitted(self):
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.generate_content(prompt="hello", model="gpt-5.5"))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert "verbosity" not in kwargs

    def test_verbosity_dropped_for_unsupported_model(self):
        """gpt-4o doesn't accept verbosity — silently drop."""
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.generate_content(
            prompt="hello",
            model="gpt-4o",
            verbosity="medium",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert "verbosity" not in kwargs

    def test_verbosity_dropped_for_o3(self):
        """o-series reasoning models also don't take verbosity."""
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.generate_content(
            prompt="hello",
            model="o3",
            verbosity="high",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert "verbosity" not in kwargs

    def test_verbosity_passed_via_chat(self):
        """chat() should also forward verbosity for supported models."""
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.chat(
            messages=[{"role": "user", "content": "hi"}],
            model="gpt-5.5",
            verbosity="medium",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert kwargs.get("verbosity") == "medium"

    def test_verbosity_dropped_via_chat_for_unsupported_model(self):
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.chat(
            messages=[{"role": "user", "content": "hi"}],
            model="gpt-4o",
            verbosity="low",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert "verbosity" not in kwargs


class TestImageGenerationModelTooltip:
    """Image generation node's model tooltip describes the GPT Image variants."""

    def test_tooltip_describes_gpt_image_models(self):
        cls = _import_node("image_nodes", "OpenAIImageGeneration")
        schema = cls.define_schema()
        model_inputs = [i for i in schema.inputs if i.id == "model"]
        assert len(model_inputs) == 1
        tooltip = model_inputs[0].tooltip or ""
        assert "gpt-image" in tooltip.lower()

    def test_gpt_image_1_mini_in_options(self):
        cls = _import_node("image_nodes", "OpenAIImageGeneration")
        schema = cls.define_schema()
        model_inputs = [i for i in schema.inputs if i.id == "model"]
        assert "gpt-image-1-mini" in model_inputs[0].options
