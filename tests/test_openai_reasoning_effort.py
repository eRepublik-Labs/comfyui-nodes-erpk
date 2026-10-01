# ABOUTME: Tests for the OpenAI reasoning_effort and verbosity parameters
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


class TestDropdownOrder:
    def test_default_model_appears_first_in_dropdown(self):
        """The default text model leads the model dropdown."""
        from openai.nodes import TEXT_MODELS
        assert TEXT_MODELS[0] == OpenAIClient.DEFAULT_MODEL


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
        # verbosity=low returned 200 on chat.completions: gpt-6 tiers
        # 2026-09-23, gpt-6.1-sol 2026-10-01.
        "gpt-6.1-sol", "gpt-6-astra", "gpt-6-sol", "gpt-6-luna",
        "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna",
    ])
    def test_reasoning_tiers_in_verbosity_models(self, model_id):
        assert model_id in OpenAIClient.VERBOSITY_MODELS, (
            f"{model_id} should accept the verbosity parameter"
        )

    def test_chat_latest_excluded_from_verbosity(self):
        # chat-latest's model page does not list verbosity.
        assert "chat-latest" not in OpenAIClient.VERBOSITY_MODELS


def _make_client_with_mock_sdk():
    """Build an OpenAIClient instance with the SDK mocked out (no __init__)."""
    client = OpenAIClient.__new__(OpenAIClient)
    client.model_name = "chat-latest"
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
            model="gpt-6.1-sol",
            reasoning_effort="high",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert kwargs.get("reasoning_effort") == "high"

    def test_reasoning_effort_dropped_for_non_reasoning_model(self):
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.generate_content(
            prompt="hello",
            model="chat-latest",
            reasoning_effort="high",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert "reasoning_effort" not in kwargs

    def test_reasoning_effort_passed_for_gpt_6_luna(self):
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.generate_content(
            prompt="hello",
            model="gpt-6-luna",
            reasoning_effort="medium",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert kwargs.get("reasoning_effort") == "medium"

    def test_reasoning_effort_none_not_passed(self):
        """When reasoning_effort is None (default), it is never passed."""
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.generate_content(
            prompt="hello",
            model="gpt-6.1-sol",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert "reasoning_effort" not in kwargs

    def test_reasoning_effort_passed_via_chat(self):
        """chat() should forward reasoning_effort for reasoning models."""
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.chat(
            messages=[{"role": "user", "content": "hi"}],
            model="gpt-6.1-sol",
            reasoning_effort="xhigh",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert kwargs.get("reasoning_effort") == "xhigh"

    def test_reasoning_effort_dropped_via_chat_for_non_reasoning(self):
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.chat(
            messages=[{"role": "user", "content": "hi"}],
            model="chat-latest",
            reasoning_effort="low",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert "reasoning_effort" not in kwargs


class TestVerbosityPassThrough:
    """verbosity is forwarded only when (a) value != 'default' and (b) model in VERBOSITY_MODELS."""

    def test_verbosity_passed_for_gpt_6_1_sol(self):
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.generate_content(
            prompt="hello",
            model="gpt-6.1-sol",
            verbosity="low",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert kwargs.get("verbosity") == "low"

    def test_verbosity_passed_for_gpt_6_astra(self):
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.generate_content(
            prompt="hello",
            model="gpt-6-astra",
            verbosity="high",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert kwargs.get("verbosity") == "high"

    def test_verbosity_dropped_when_default(self):
        """'default' is the no-op marker — never sent over the wire."""
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.generate_content(
            prompt="hello",
            model="gpt-6.1-sol",
            verbosity="default",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert "verbosity" not in kwargs

    def test_verbosity_dropped_when_omitted(self):
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.generate_content(prompt="hello", model="gpt-6.1-sol"))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert "verbosity" not in kwargs

    def test_verbosity_dropped_for_unsupported_model(self):
        """chat-latest doesn't accept verbosity — silently drop."""
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.generate_content(
            prompt="hello",
            model="chat-latest",
            verbosity="medium",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert "verbosity" not in kwargs

    def test_verbosity_passed_via_chat(self):
        """chat() should also forward verbosity for supported models."""
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.chat(
            messages=[{"role": "user", "content": "hi"}],
            model="gpt-6.1-sol",
            verbosity="medium",
        ))

        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        assert kwargs.get("verbosity") == "medium"

    def test_verbosity_dropped_via_chat_for_unsupported_model(self):
        client, mock_sdk = _make_client_with_mock_sdk()

        asyncio.run(client.chat(
            messages=[{"role": "user", "content": "hi"}],
            model="chat-latest",
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


class TestSamplingParamsNeverSent:
    """Every offered text model rejects sampling params on chat.completions
    (measured: temperature 0.7 -> 400 "Only the default (1) value is
    supported" on gpt-6.1-sol and chat-latest; top_p and stop -> 400
    unsupported_parameter on gpt-6.1-sol). The node's temperature, top_p and
    stop_sequences widgets stay for saved-workflow positions, so the client
    must drop their values rather than earn a 400."""

    @pytest.mark.parametrize("model_id", sorted(OpenAIClient.MODELS))
    def test_generate_content_drops_sampling_params(self, model_id):
        client, mock_sdk = _make_client_with_mock_sdk()
        asyncio.run(client.generate_content(
            prompt="hello", model=model_id,
            temperature=0.7, top_p=0.5, stop_sequences=["x"],
        ))
        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        for param in ("temperature", "top_p", "stop"):
            assert param not in kwargs, f"{param} sent to {model_id}"

    @pytest.mark.parametrize("model_id", sorted(OpenAIClient.MODELS))
    def test_chat_drops_sampling_params(self, model_id):
        client, mock_sdk = _make_client_with_mock_sdk()
        asyncio.run(client.chat(
            messages=[{"role": "user", "content": "hi"}], model=model_id,
            temperature=0.7, top_p=0.5, stop_sequences=["x"],
        ))
        kwargs = mock_sdk.chat.completions.create.call_args.kwargs
        for param in ("temperature", "top_p", "stop"):
            assert param not in kwargs, f"{param} sent to {model_id}"

    def test_chat_latest_gets_no_reasoning_effort(self):
        client, mock_sdk = _make_client_with_mock_sdk()
        asyncio.run(client.generate_content(
            prompt="hello", model="chat-latest", reasoning_effort="minimal",
        ))
        assert "reasoning_effort" not in mock_sdk.chat.completions.create.call_args.kwargs


class TestMinimalEffortClamp:
    """'minimal' 400s on every kept reasoning model (gpt-5.6 and gpt-6.x,
    measured 2026-09-23 and 2026-10-01), so the client sends 'low'."""

    @pytest.mark.parametrize("model_id", sorted(OpenAIClient.REASONING_MODELS))
    def test_minimal_reaches_api_as_low(self, model_id):
        client, mock_sdk = _make_client_with_mock_sdk()
        asyncio.run(client.generate_content(
            prompt="hello", model=model_id, reasoning_effort="minimal",
        ))
        assert mock_sdk.chat.completions.create.call_args.kwargs["reasoning_effort"] == "low"
