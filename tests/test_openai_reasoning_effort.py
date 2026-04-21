# ABOUTME: Tests for OpenAI reasoning_effort parameter and gpt-5.4 family models
# ABOUTME: Validates schema inputs, SDK pass-through for reasoning models, and drop for non-reasoning

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

        client.generate_content(
            prompt="hello",
            model="gpt-5.4",
            reasoning_effort="high",
        )

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert kwargs.get("reasoning_effort") == "high"

    def test_reasoning_effort_dropped_for_non_reasoning_model(self):
        client, mock_sdk = _make_client_with_mock_sdk()

        client.generate_content(
            prompt="hello",
            model="gpt-4o",
            reasoning_effort="high",
        )

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert "reasoning_effort" not in kwargs

    def test_reasoning_effort_passed_for_o3(self):
        client, mock_sdk = _make_client_with_mock_sdk()

        client.generate_content(
            prompt="hello",
            model="o3",
            reasoning_effort="medium",
        )

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert kwargs.get("reasoning_effort") == "medium"

    def test_reasoning_effort_none_not_passed(self):
        """When reasoning_effort is None (default), it is never passed."""
        client, mock_sdk = _make_client_with_mock_sdk()

        client.generate_content(
            prompt="hello",
            model="gpt-5.4",
        )

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert "reasoning_effort" not in kwargs

    def test_reasoning_effort_passed_via_chat(self):
        """chat() should forward reasoning_effort for reasoning models."""
        client, mock_sdk = _make_client_with_mock_sdk()

        client.chat(
            messages=[{"role": "user", "content": "hi"}],
            model="gpt-5.4-pro",
            reasoning_effort="xhigh",
        )

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert kwargs.get("reasoning_effort") == "xhigh"

    def test_reasoning_effort_dropped_via_chat_for_non_reasoning(self):
        client, mock_sdk = _make_client_with_mock_sdk()

        client.chat(
            messages=[{"role": "user", "content": "hi"}],
            model="gpt-4o",
            reasoning_effort="low",
        )

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert "reasoning_effort" not in kwargs


class TestDallE3DeprecationTooltip:
    """Image generation node's model tooltip warns about dall-e-3 deprecation."""

    def test_tooltip_mentions_dall_e_3_deprecation(self):
        cls = _import_node("image_nodes", "OpenAIImageGeneration")
        schema = cls.define_schema()
        model_inputs = [i for i in schema.inputs if i.id == "model"]
        assert len(model_inputs) == 1
        tooltip = model_inputs[0].tooltip or ""
        assert "dall-e-3" in tooltip.lower()
        assert "deprecated" in tooltip.lower()

    def test_gpt_image_1_mini_in_options(self):
        cls = _import_node("image_nodes", "OpenAIImageGeneration")
        schema = cls.define_schema()
        model_inputs = [i for i in schema.inputs if i.id == "model"]
        assert "gpt-image-1-mini" in model_inputs[0].options
