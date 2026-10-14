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
from tests.openai_sdk_signature import assert_binds


# Mirrors ComfyUI's own OpenAI node (comfy_api_nodes/nodes_openai.py, v0.39.2):
# "default" sends no effort and is the starting value; "none" turns reasoning off.
REASONING_EFFORT_OPTIONS = ["default", "none", "minimal", "low", "medium", "high", "xhigh"]
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
        assert inp.options == REASONING_EFFORT_OPTIONS
        assert inp.default == "default"

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


# Measured 2026-10-14 on chat.completions: reasoning_effort "none" returns 200
# on these five and 400 on gpt-6.1-sol and gpt-6-astra; with effort none,
# temperature 0.7 and top_p 0.9 return 200 on the five, while stop still 400s.
ACCEPTS_EFFORT_NONE = ["gpt-6-sol", "gpt-6-luna", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"]
REJECTS_EFFORT_NONE = ["gpt-6.1-sol", "gpt-6-astra"]


def _run_node(class_name, model, **inputs):
    """Run a text node through the real client with only the SDK mocked."""
    client, mock_sdk = _make_client_with_mock_sdk()
    cls = _import_node("nodes", class_name)
    if class_name == "OpenAIVision":
        torch = pytest.importorskip("torch")
        asyncio.run(cls.execute(torch.zeros(1, 8, 8, 3), "describe", client=client, model=model, **inputs))
    else:
        asyncio.run(cls.execute("hello", client=client, model=model, **inputs))
    return mock_sdk.chat.completions.create.call_args.kwargs


TEXT_NODES = ["OpenAITextGeneration", "OpenAIChat", "OpenAIVision"]


class TestEffortNone:
    """The widget's 'none' sends a real reasoning_effort 'none' (no reasoning)
    where the model accepts it, and is omitted (model default) where it 400s."""

    @pytest.mark.parametrize("class_name", TEXT_NODES)
    @pytest.mark.parametrize("model_id", ACCEPTS_EFFORT_NONE)
    def test_none_is_sent_where_accepted(self, class_name, model_id):
        kwargs = _run_node(class_name, model_id, reasoning_effort="none")
        assert kwargs["reasoning_effort"] == "none"

    @pytest.mark.parametrize("class_name", TEXT_NODES)
    @pytest.mark.parametrize("model_id", ACCEPTS_EFFORT_NONE + REJECTS_EFFORT_NONE)
    def test_default_sends_no_effort_and_no_sampling(self, class_name, model_id):
        kwargs = _run_node(class_name, model_id, reasoning_effort="default", temperature=0.7, top_p=0.9)
        assert "reasoning_effort" not in kwargs
        assert "temperature" not in kwargs
        assert "top_p" not in kwargs

    @pytest.mark.parametrize("class_name", TEXT_NODES)
    @pytest.mark.parametrize("model_id", REJECTS_EFFORT_NONE)
    def test_none_is_omitted_where_rejected(self, class_name, model_id):
        kwargs = _run_node(class_name, model_id, reasoning_effort="none")
        assert "reasoning_effort" not in kwargs

    @pytest.mark.parametrize("class_name", ["OpenAITextGeneration", "OpenAIChat"])
    @pytest.mark.parametrize("model_id", ACCEPTS_EFFORT_NONE)
    def test_effort_none_lets_temperature_and_top_p_through(self, class_name, model_id):
        kwargs = _run_node(
            class_name, model_id, reasoning_effort="none",
            temperature=0.7, top_p=0.9, stop_sequences="zzz",
        )
        assert kwargs["temperature"] == 0.7
        assert kwargs["top_p"] == 0.9
        assert "stop" not in kwargs

    @pytest.mark.parametrize("model_id", ACCEPTS_EFFORT_NONE)
    def test_vision_effort_none_sends_temperature(self, model_id):
        kwargs = _run_node("OpenAIVision", model_id, reasoning_effort="none", temperature=0.4)
        assert kwargs["temperature"] == 0.4

    @pytest.mark.parametrize("class_name", ["OpenAITextGeneration", "OpenAIChat"])
    @pytest.mark.parametrize("model_id", REJECTS_EFFORT_NONE + ["chat-latest"])
    def test_sampling_still_dropped_without_a_real_none(self, class_name, model_id):
        kwargs = _run_node(
            class_name, model_id, reasoning_effort="none",
            temperature=0.7, top_p=0.9, stop_sequences="zzz",
        )
        for param in ("temperature", "top_p", "stop"):
            assert param not in kwargs, f"{param} sent to {model_id}"

    @pytest.mark.parametrize("model_id", ACCEPTS_EFFORT_NONE)
    def test_sampling_dropped_when_effort_is_not_none(self, model_id):
        kwargs = _run_node(
            "OpenAITextGeneration", model_id, reasoning_effort="low",
            temperature=0.7, top_p=0.9,
        )
        assert "temperature" not in kwargs
        assert "top_p" not in kwargs


# The schema the 2026-10-14 probe sent with strict:true (200 on all 8 models).
STRICT_SCHEMA = {
    "type": "object",
    "properties": {"a": {"type": "integer"}},
    "required": ["a"],
    "additionalProperties": False,
}


class TestJsonSchemaResponseFormat:
    """Strict Structured Outputs (response_format json_schema) on the text and
    chat nodes. The schema is a String widget appended last, so saved
    workflows keep their widget slots."""

    @pytest.mark.parametrize("class_name", ["OpenAITextGeneration", "OpenAIChat"])
    def test_schema_options_and_widget(self, class_name):
        inputs = _import_node("nodes", class_name).define_schema().inputs
        response_format = next(i for i in inputs if i.id == "response_format")
        assert response_format.options == ["default", "json_object", "json_schema"]
        last = inputs[-1]
        assert last.id == "json_schema"
        assert last.optional is True
        assert last.multiline is True

    @pytest.mark.parametrize("class_name", ["OpenAITextGeneration", "OpenAIChat"])
    def test_schema_sent_strict(self, class_name):
        import json
        kwargs = _run_node(
            class_name, "gpt-6-luna",
            response_format="json_schema", json_schema=json.dumps(STRICT_SCHEMA),
        )
        assert_binds(kwargs, "openai.resources.chat.completions", "Completions", "create")
        assert kwargs["response_format"] == {
            "type": "json_schema",
            "json_schema": {"name": "response", "strict": True, "schema": STRICT_SCHEMA},
        }

    @pytest.mark.parametrize("class_name", ["OpenAITextGeneration", "OpenAIChat"])
    @pytest.mark.parametrize("schema,message", [
        ("{not json", r"json_schema is not valid JSON: Expecting property name"),
        ("", r"response_format 'json_schema' needs a JSON Schema in the json_schema input"),
        ("[1, 2]", r"json_schema must be a JSON object \(a JSON Schema\), got list"),
    ])
    def test_bad_schema_refused_before_the_call(self, class_name, schema, message):
        client, mock_sdk = _make_client_with_mock_sdk()
        cls = _import_node("nodes", class_name)
        with pytest.raises(ValueError, match=message):
            asyncio.run(cls.execute(
                "hello", client=client, model="gpt-6-luna",
                response_format="json_schema", json_schema=schema,
            ))
        mock_sdk.chat.completions.create.assert_not_called()

    def test_schema_ignored_unless_selected(self):
        kwargs = _run_node(
            "OpenAITextGeneration", "gpt-6-luna",
            response_format="json_object", json_schema="{not json",
        )
        assert kwargs["response_format"] == {"type": "json_object"}


class TestVisionDetail:
    """image_url.detail 'original' returns 200 on all 8 models (measured
    2026-10-14); the chat reference lists auto|low|high|original."""

    def test_detail_offers_original(self):
        inputs = _import_node("nodes", "OpenAIVision").define_schema().inputs
        detail = next(i for i in inputs if i.id == "detail")
        assert detail.options == ["auto", "low", "high", "original"]

    def test_original_reaches_the_image_part(self):
        kwargs = _run_node("OpenAIVision", "gpt-6-luna", detail="original")
        image_parts = [p for p in kwargs["messages"][-1]["content"] if p["type"] == "image_url"]
        assert [p["image_url"]["detail"] for p in image_parts] == ["original"]
