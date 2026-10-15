# ABOUTME: Tests for the Responses-API image generation path.
# ABOUTME: Covers client.generate_image_via_responses() and the OpenAIImageResponses node.

"""
Tests for the OpenAI Responses API image_generation tool integration.

Validates that:
- client.generate_image_via_responses builds the right request shape
- image_generation tool has the expected model/size/quality fields
- web_search tool is added when enable_web_search=True
- reasoning config is added unless the effort is omitted ("default", or "none" on a mainline that rejects it)
- gpt-image-2 size validation runs for gpt-image-2 image_model
- Response parsing collects images, revised_prompt, reasoning_summary
- OpenAIImageResponses node schema exposes the expected inputs/outputs
"""

import asyncio
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# Stub APIError on the local openai package (which shadows the SDK in tests)
import openai as _local_openai
if not hasattr(_local_openai, "APIError"):
    _local_openai.APIError = type("APIError", (Exception,), {})

from openai.openai_api.client import OpenAIClient  # noqa: E402
from tests.openai_sdk_signature import assert_binds  # noqa: E402


def _make_client_with_mock_response(output_items):
    """Build an OpenAIClient with client.responses.create returning a mocked response."""
    client = OpenAIClient.__new__(OpenAIClient)
    mock_sdk = MagicMock()
    mock_response = SimpleNamespace(status="completed", output=output_items)
    mock_sdk.responses.create.return_value = mock_response
    client.client = mock_sdk
    client.system_instruction = None
    return client, mock_sdk


def _image_call(result="fakebase64data", revised=None, status="completed"):
    """Build a mock image_generation_call output item."""
    obj = SimpleNamespace(type="image_generation_call", result=result, status=status)
    if revised is not None:
        obj.revised_prompt = revised
    return obj


def _reasoning_item(text="some reasoning"):
    """Build a mock reasoning output item with a summary part."""
    part = SimpleNamespace(text=text)
    return SimpleNamespace(type="reasoning", summary=[part])


def _message_item():
    """Mainline model's accompanying text response (ignored by the image path)."""
    return SimpleNamespace(type="message", content=[])


class TestRequestShape:
    """generate_image_via_responses builds the correct request body."""

    def test_minimal_request_has_model_input_tools(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        asyncio.run(client.generate_image_via_responses(
            prompt="a red apple",
            mainline_model="gpt-6-sol",
            image_model="gpt-image-2",
            size="1024x1024",
        ))
        args = sdk.responses.create.call_args.kwargs
        assert args["model"] == "gpt-6-sol"
        assert args["input"] == "a red apple"
        assert isinstance(args["tools"], list)
        assert args["tools"][0]["type"] == "image_generation"
        assert args["tools"][0]["model"] == "gpt-image-2"

    def test_reasoning_omitted_when_default(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        asyncio.run(client.generate_image_via_responses(
            prompt="x", image_model="gpt-image-2", reasoning_effort="default",
        ))
        args = sdk.responses.create.call_args.kwargs
        assert "reasoning" not in args

    @pytest.mark.parametrize("mainline", ["gpt-6-sol", "gpt-6-luna", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"])
    def test_none_effort_is_sent_where_the_mainline_accepts_it(self, mainline):
        # Responses effort "none" measured 200 on these mainlines (2026-10-14 study).
        client, sdk = _make_client_with_mock_response([_image_call()])
        asyncio.run(client.generate_image_via_responses(
            prompt="x", mainline_model=mainline, image_model="gpt-image-2", reasoning_effort="none",
        ))
        assert sdk.responses.create.call_args.kwargs["reasoning"]["effort"] == "none"

    @pytest.mark.parametrize("mainline", ["gpt-6.1-sol", "gpt-6-astra"])
    def test_none_effort_is_omitted_where_the_mainline_rejects_it(self, mainline):
        client, sdk = _make_client_with_mock_response([_image_call()])
        asyncio.run(client.generate_image_via_responses(
            prompt="x", mainline_model=mainline, image_model="gpt-image-2", reasoning_effort="none",
        ))
        assert "reasoning" not in sdk.responses.create.call_args.kwargs

    def test_reasoning_added_when_effort_set(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        asyncio.run(client.generate_image_via_responses(
            prompt="x", image_model="gpt-image-2", reasoning_effort="medium",
        ))
        args = sdk.responses.create.call_args.kwargs
        assert args["reasoning"]["effort"] == "medium"
        assert args["reasoning"]["summary"] == "auto"

    def test_web_search_tool_added_when_enabled(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        asyncio.run(client.generate_image_via_responses(
            prompt="x", image_model="gpt-image-2", enable_web_search=True,
        ))
        tools = sdk.responses.create.call_args.kwargs["tools"]
        tool_types = [t["type"] for t in tools]
        assert "image_generation" in tool_types
        assert "web_search" in tool_types

    def test_web_search_tool_omitted_when_disabled(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        asyncio.run(client.generate_image_via_responses(
            prompt="x", image_model="gpt-image-2", enable_web_search=False,
        ))
        tools = sdk.responses.create.call_args.kwargs["tools"]
        assert len(tools) == 1
        assert tools[0]["type"] == "image_generation"

    def test_non_default_params_present_in_tool_config(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        asyncio.run(client.generate_image_via_responses(
            prompt="x",
            image_model="gpt-image-2",
            size="1536x1024",
            quality="high",
            background="opaque",
            output_format="jpeg",
            moderation="low",
            action="generate",
        ))
        tool = sdk.responses.create.call_args.kwargs["tools"][0]
        assert tool["size"] == "1536x1024"
        assert tool["quality"] == "high"
        assert tool["background"] == "opaque"
        assert tool["output_format"] == "jpeg"
        assert tool["moderation"] == "low"
        assert tool["action"] == "generate"

    def test_default_params_omitted_from_tool_config(self):
        """Match the existing 'auto' = 'don't send' pattern from generate_image."""
        client, sdk = _make_client_with_mock_response([_image_call()])
        asyncio.run(client.generate_image_via_responses(
            prompt="x",
            image_model="gpt-image-2",
            quality="auto",
            background="auto",
            moderation="auto",
            output_format="png",
        ))
        tool = sdk.responses.create.call_args.kwargs["tools"][0]
        assert "quality" not in tool
        assert "background" not in tool
        assert "moderation" not in tool
        # output_format defaults to png and we omit it too (API default)
        assert "output_format" not in tool


class TestEffortAndQualityClamps:
    """Measured 2026-10-01 on responses.create with the image_generation tool:
    reasoning.effort 'minimal' 400s on every model ("cannot be used with
    reasoning.effort 'minimal': image_gen") and 'none' 400s on gpt-6.1-sol.
    The images reference gives xhigh/max only to GPT Image 2.5."""

    def test_minimal_effort_clamps_to_low(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        asyncio.run(client.generate_image_via_responses(
            prompt="x", mainline_model="gpt-6.1-sol", reasoning_effort="minimal",
        ))
        assert sdk.responses.create.call_args.kwargs["reasoning"]["effort"] == "low"

    def test_effort_omitted_for_non_reasoning_mainline(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        asyncio.run(client.generate_image_via_responses(
            prompt="x", mainline_model="chat-latest", reasoning_effort="high",
        ))
        assert "reasoning" not in sdk.responses.create.call_args.kwargs

    def test_extended_quality_reaches_2_5(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        asyncio.run(client.generate_image_via_responses(
            prompt="x", image_model="gpt-image-2.5-sunburst", quality="max",
        ))
        assert sdk.responses.create.call_args.kwargs["tools"][0]["quality"] == "max"

    def test_extended_quality_clamps_on_gpt_image_2(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        asyncio.run(client.generate_image_via_responses(
            prompt="x", image_model="gpt-image-2", quality="xhigh",
        ))
        assert sdk.responses.create.call_args.kwargs["tools"][0]["quality"] == "high"


class TestVerbosity:
    """Responses.create() has no `verbosity` keyword (SDK 2.15, 2.38, 3.31),
    and the server rejects a top-level one: 400 "this parameter has moved to
    'text.verbosity'" on all 7 mainlines, while text.verbosity=low returns
    200 (measured 2026-10-14)."""

    def test_verbosity_is_sent_as_text_verbosity(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        asyncio.run(client.generate_image_via_responses(
            prompt="x", mainline_model="gpt-6-luna", verbosity="low",
        ))
        params = sdk.responses.create.call_args.kwargs
        assert_binds(params, "openai.resources.responses", "Responses", "create")
        assert params["text"] == {"verbosity": "low"}

    def test_default_verbosity_sends_no_text_config(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        asyncio.run(client.generate_image_via_responses(
            prompt="x", mainline_model="gpt-6-luna", verbosity="default",
        ))
        assert "text" not in sdk.responses.create.call_args.kwargs


MAINLINES = [
    "gpt-6.1-sol", "gpt-6-astra", "gpt-6-sol", "gpt-6-luna",
    "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna",
]


class TestResponsesOnlyOptions:
    """Measured 2026-10-14 on responses.create with the image_generation tool
    (tool_choice none): reasoning.effort 'max' and reasoning.mode 'pro' return
    200 on all 7 mainlines, mode 'pro' also without an effort (it then reasons
    at medium); the tool accepts size 'auto' and output_compression with jpeg."""

    @pytest.mark.parametrize("mainline", MAINLINES)
    def test_max_effort_reaches_every_mainline(self, mainline):
        client, sdk = _make_client_with_mock_response([_image_call()])
        asyncio.run(client.generate_image_via_responses(
            prompt="x", mainline_model=mainline, reasoning_effort="max",
        ))
        assert sdk.responses.create.call_args.kwargs["reasoning"]["effort"] == "max"

    def test_pro_mode_rides_with_the_effort(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        asyncio.run(client.generate_image_via_responses(
            prompt="x", mainline_model="gpt-6-luna", reasoning_effort="low", reasoning_mode="pro",
        ))
        assert sdk.responses.create.call_args.kwargs["reasoning"] == {
            "effort": "low", "summary": "auto", "mode": "pro",
        }

    def test_pro_mode_without_effort(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        asyncio.run(client.generate_image_via_responses(
            prompt="x", mainline_model="gpt-6.1-sol", reasoning_effort="none", reasoning_mode="pro",
        ))
        assert sdk.responses.create.call_args.kwargs["reasoning"] == {"mode": "pro"}

    def test_standard_mode_sends_no_mode(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        asyncio.run(client.generate_image_via_responses(
            prompt="x", mainline_model="gpt-6-luna", reasoning_effort="low", reasoning_mode="standard",
        ))
        assert "mode" not in sdk.responses.create.call_args.kwargs["reasoning"]

    @pytest.mark.parametrize("output_format", ["jpeg", "webp"])
    def test_output_compression_sent_for_lossy_formats(self, output_format):
        client, sdk = _make_client_with_mock_response([_image_call()])
        asyncio.run(client.generate_image_via_responses(
            prompt="x", output_format=output_format, output_compression=50,
        ))
        tool = sdk.responses.create.call_args.kwargs["tools"][0]
        assert tool["output_format"] == output_format
        assert tool["output_compression"] == 50

    def test_output_compression_not_sent_for_png(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        asyncio.run(client.generate_image_via_responses(
            prompt="x", output_format="png", output_compression=50,
        ))
        tool = sdk.responses.create.call_args.kwargs["tools"][0]
        assert "output_compression" not in tool
        assert "output_format" not in tool

    def test_every_option_at_once_binds_to_the_sdk(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        client.system_instruction = "be brief"
        asyncio.run(client.generate_image_via_responses(
            prompt="x", mainline_model="gpt-6-luna", image_model="gpt-image-2.5-flare",
            reasoning_effort="max", reasoning_mode="pro", verbosity="low", size="auto",
            quality="max", background="transparent", output_format="webp",
            output_compression=80, moderation="low", enable_web_search=True,
        ))
        assert_binds(sdk.responses.create.call_args.kwargs,
                     "openai.resources.responses", "Responses", "create")


class TestNodeForwardsNewWidgets:
    def test_reasoning_mode_and_compression_reach_the_request(self):
        pytest.importorskip("torch")
        import base64
        import io
        from PIL import Image
        # Through the erpk package, so the node's relative imports
        # resolve as they do inside ComfyUI.
        from erpk.openai.image_nodes import OpenAIImageResponses

        png = io.BytesIO()
        Image.new("RGB", (4, 4)).save(png, "PNG")
        client, sdk = _make_client_with_mock_response(
            [_image_call(result=base64.b64encode(png.getvalue()).decode())]
        )
        asyncio.run(OpenAIImageResponses.execute(
            "x", client=client, mainline_model="gpt-6-luna", reasoning_effort="max",
            reasoning_mode="pro", size="auto", output_format="jpeg", output_compression=40,
        ))
        params = sdk.responses.create.call_args.kwargs
        assert params["reasoning"]["mode"] == "pro"
        assert params["reasoning"]["effort"] == "max"
        assert params["tools"][0]["output_compression"] == 40
        assert "size" not in params["tools"][0]


class TestGptImage2SizeValidation:
    """Size preflight runs for gpt-image-2 in the Responses path."""

    def test_below_min_pixels_raises_before_api_call(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        with pytest.raises(ValueError, match="at least 655,360"):
            asyncio.run(client.generate_image_via_responses(
                prompt="x", image_model="gpt-image-2", size="512x512",
            ))
        assert not sdk.responses.create.called, "API must not be called when preflight fails"



class TestBackgroundPassThrough:
    """gpt-image-2 rejects transparent (400, measured 2026-10-01); 2.5 takes it."""

    def test_transparent_rejected_before_the_call_on_gpt_image_2(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        with pytest.raises(ValueError, match="gpt-image-2 does not support background='transparent'"):
            asyncio.run(client.generate_image_via_responses(
                prompt="x", image_model="gpt-image-2",
                size="1024x1024", background="transparent",
            ))
        sdk.responses.create.assert_not_called()

    def test_transparent_preserved_for_gpt_image_2_5(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        asyncio.run(client.generate_image_via_responses(
            prompt="x", image_model="gpt-image-2.5-flare", background="transparent",
        ))
        tool = sdk.responses.create.call_args.kwargs["tools"][0]
        assert tool["background"] == "transparent"


class TestResponseParsing:
    """Response output items parsed correctly into images/revised_prompt/reasoning_summary."""

    def test_single_image_call_returns_one_image(self):
        client, _ = _make_client_with_mock_response([
            _image_call(result="AAAA", revised="a revised prompt"),
            _message_item(),
        ])
        result = asyncio.run(client.generate_image_via_responses(
            prompt="x", image_model="gpt-image-2", size="1024x1024",
        ))
        assert result["images"] == ["AAAA"]
        assert "a revised prompt" in result["revised_prompt"]
        assert result["reasoning_summary"] == ""

    def test_multiple_image_calls_collected(self):
        client, _ = _make_client_with_mock_response([
            _image_call(result="IMG1"),
            _image_call(result="IMG2"),
            _message_item(),
        ])
        result = asyncio.run(client.generate_image_via_responses(
            prompt="x", image_model="gpt-image-2", size="1024x1024",
        ))
        assert result["images"] == ["IMG1", "IMG2"]

    def test_reasoning_summary_extracted(self):
        client, _ = _make_client_with_mock_response([
            _reasoning_item(text="I considered multiple options..."),
            _image_call(result="IMG"),
            _message_item(),
        ])
        result = asyncio.run(client.generate_image_via_responses(
            prompt="x", image_model="gpt-image-2",
            size="1024x1024", reasoning_effort="medium",
        ))
        assert "considered multiple options" in result["reasoning_summary"]

    def test_empty_output_returns_empty_images(self):
        client, _ = _make_client_with_mock_response([])
        result = asyncio.run(client.generate_image_via_responses(
            prompt="x", image_model="gpt-image-2", size="1024x1024",
        ))
        assert result["images"] == []
        assert result["revised_prompt"] == ""
        assert result["reasoning_summary"] == ""


class TestNodeSchema:
    """OpenAIImageResponses node exposes the expected inputs/outputs."""

    @pytest.fixture
    def schema(self):
        from openai.image_nodes import OpenAIImageResponses
        return OpenAIImageResponses.define_schema()

    def test_node_id(self, schema):
        assert schema.node_id == "OpenAIImageResponses"

    def test_category(self, schema):
        assert schema.category == "ERPK/OpenAI"

    def test_not_idempotent(self, schema):
        assert schema.not_idempotent is True

    def test_has_mainline_model_input(self, schema):
        inp = next((i for i in schema.inputs if i.id == "mainline_model"), None)
        assert inp is not None
        # Each returned 200 on responses.create with the image_generation tool
        # attached (tool_choice="none", measured 2026-10-01).
        assert set(inp.options) == {
            "gpt-6.1-sol", "gpt-6-astra", "gpt-6-sol", "gpt-6-luna",
            "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna",
        }
        assert inp.default == "gpt-6.1-sol"

    def test_has_image_model_input(self, schema):
        inp = next((i for i in schema.inputs if i.id == "image_model"), None)
        assert inp is not None
        # The 2.5 model pages: "Select it directly in the Image API or as the
        # model of the Responses API image generation tool."
        assert set(inp.options) == {"gpt-image-2.5-sunburst", "gpt-image-2.5-flare", "gpt-image-2"}
        assert inp.default == "gpt-image-2"

    def test_quality_offers_extended_tiers(self, schema):
        inp = next(i for i in schema.inputs if i.id == "quality")
        assert inp.options == ["auto", "low", "medium", "high", "xhigh", "max"]

    def test_has_reasoning_effort_input(self, schema):
        inp = next((i for i in schema.inputs if i.id == "reasoning_effort"), None)
        assert inp is not None
        assert inp.options == ["default", "none", "minimal", "low", "medium", "high", "xhigh", "max"]
        assert inp.default == "default"

    def test_text_nodes_never_offer_max(self):
        # max returns 400 on chat.completions on all 7 (measured 2026-10-14).
        from openai.nodes import REASONING_EFFORT_OPTIONS
        assert "max" not in REASONING_EFFORT_OPTIONS

    def test_size_offers_auto(self, schema):
        inp = next(i for i in schema.inputs if i.id == "size")
        assert inp.options[0] == "auto"

    def test_new_widgets_appended_last(self, schema):
        assert [i.id for i in schema.inputs][-2:] == ["reasoning_mode", "output_compression"]
        mode = schema.inputs[-2]
        assert mode.options == ["standard", "pro"]
        assert mode.default == "standard"
        compression = schema.inputs[-1]
        assert (compression.min, compression.max, compression.default) == (0, 100, 100)

    def test_has_enable_web_search_input(self, schema):
        inp = next((i for i in schema.inputs if i.id == "enable_web_search"), None)
        assert inp is not None
        assert inp.io_type == "BOOLEAN"
        assert inp.default is False

    def test_has_three_outputs(self, schema):
        output_ids = [o.id for o in schema.outputs]
        assert "image" in output_ids
        assert "revised_prompt" in output_ids
        assert "reasoning_summary" in output_ids


class TestOpenAIPackageRegistration:
    """The new node must be exported via openai.NODES."""

    def test_responses_node_in_nodes_list(self):
        import importlib
        mod = importlib.import_module("openai")
        node_names = [cls.__name__ for cls in mod.NODES]
        assert "OpenAIImageResponses" in node_names


class TestSystemInstruction:
    """A configured system instruction reaches the Responses API.

    The Responses API takes an `instructions` parameter and honours it
    (verified live on 2026-09-17). The images endpoints have no equivalent, so
    this node is the only image path where the OpenAI System Instruction node
    can do anything at all.
    """

    def test_instruction_is_forwarded_as_instructions(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        client.system_instruction = "Render everything as a pencil sketch."

        asyncio.run(client.generate_image_via_responses(prompt="a cat"))

        assert sdk.responses.create.call_args.kwargs["instructions"] == "Render everything as a pencil sketch."

    def test_instructions_omitted_when_unset(self):
        # Sending instructions=None would override nothing but adds a null field.
        client, sdk = _make_client_with_mock_response([_image_call()])

        asyncio.run(client.generate_image_via_responses(prompt="a cat"))

        assert "instructions" not in sdk.responses.create.call_args.kwargs

    def test_instructions_omitted_when_blank(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        client.system_instruction = "   "

        asyncio.run(client.generate_image_via_responses(prompt="a cat"))

        assert "instructions" not in sdk.responses.create.call_args.kwargs

    def test_prompt_still_travels_as_input(self):
        # The instruction must not displace the prompt.
        client, sdk = _make_client_with_mock_response([_image_call()])
        client.system_instruction = "Be terse."

        asyncio.run(client.generate_image_via_responses(prompt="a cat"))

        assert sdk.responses.create.call_args.kwargs["input"] == "a cat"

