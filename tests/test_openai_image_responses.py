# ABOUTME: Tests for the Responses-API image generation path.
# ABOUTME: Covers client.generate_image_via_responses() and the OpenAIImageResponses node.

"""
Tests for the OpenAI Responses API image_generation tool integration.

Validates that:
- client.generate_image_via_responses builds the right request shape
- image_generation tool has the expected model/size/quality fields
- web_search tool is added when enable_web_search=True
- reasoning config is added only when reasoning_effort != "none"
- gpt-image-2 size validation runs for gpt-image-2 image_model
- Response parsing collects images, revised_prompt, reasoning_summary
- OpenAIImageResponses node schema exposes the expected inputs/outputs
"""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# Stub APIError on the local openai package (which shadows the SDK in tests)
import openai as _local_openai
if not hasattr(_local_openai, "APIError"):
    _local_openai.APIError = type("APIError", (Exception,), {})

from openai.openai_api.client import OpenAIClient  # noqa: E402


def _make_client_with_mock_response(output_items):
    """Build an OpenAIClient with client.responses.create returning a mocked response."""
    client = OpenAIClient.__new__(OpenAIClient)
    mock_sdk = MagicMock()
    mock_response = SimpleNamespace(status="completed", output=output_items)
    mock_sdk.responses.create.return_value = mock_response
    client.client = mock_sdk
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
        client.generate_image_via_responses(
            prompt="a red apple",
            mainline_model="gpt-5.4",
            image_model="gpt-image-2",
            size="1024x1024",
        )
        args = sdk.responses.create.call_args.kwargs
        assert args["model"] == "gpt-5.4"
        assert args["input"] == "a red apple"
        assert isinstance(args["tools"], list)
        assert args["tools"][0]["type"] == "image_generation"
        assert args["tools"][0]["model"] == "gpt-image-2"

    def test_reasoning_omitted_when_none(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        client.generate_image_via_responses(
            prompt="x", image_model="gpt-image-2", reasoning_effort="none",
        )
        args = sdk.responses.create.call_args.kwargs
        assert "reasoning" not in args

    def test_reasoning_added_when_effort_set(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        client.generate_image_via_responses(
            prompt="x", image_model="gpt-image-2", reasoning_effort="medium",
        )
        args = sdk.responses.create.call_args.kwargs
        assert args["reasoning"]["effort"] == "medium"
        assert args["reasoning"]["summary"] == "auto"

    def test_web_search_tool_added_when_enabled(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        client.generate_image_via_responses(
            prompt="x", image_model="gpt-image-2", enable_web_search=True,
        )
        tools = sdk.responses.create.call_args.kwargs["tools"]
        tool_types = [t["type"] for t in tools]
        assert "image_generation" in tool_types
        assert "web_search" in tool_types

    def test_web_search_tool_omitted_when_disabled(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        client.generate_image_via_responses(
            prompt="x", image_model="gpt-image-2", enable_web_search=False,
        )
        tools = sdk.responses.create.call_args.kwargs["tools"]
        assert len(tools) == 1
        assert tools[0]["type"] == "image_generation"

    def test_non_default_params_present_in_tool_config(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        client.generate_image_via_responses(
            prompt="x",
            image_model="gpt-image-2",
            size="1536x1024",
            quality="high",
            background="opaque",
            output_format="jpeg",
            moderation="low",
            action="generate",
        )
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
        client.generate_image_via_responses(
            prompt="x",
            image_model="gpt-image-2",
            quality="auto",
            background="auto",
            moderation="auto",
            output_format="png",
        )
        tool = sdk.responses.create.call_args.kwargs["tools"][0]
        assert "quality" not in tool
        assert "background" not in tool
        assert "moderation" not in tool
        # output_format defaults to png and we omit it too (API default)
        assert "output_format" not in tool


class TestGptImage2SizeValidation:
    """Size preflight runs for gpt-image-2 in the Responses path."""

    def test_below_min_pixels_raises_before_api_call(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        with pytest.raises(ValueError, match="at least 655,360"):
            client.generate_image_via_responses(
                prompt="x", image_model="gpt-image-2", size="512x512",
            )
        assert not sdk.responses.create.called, "API must not be called when preflight fails"

    def test_validation_skipped_for_gpt_image_1_5(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        client.generate_image_via_responses(
            prompt="x", image_model="gpt-image-1.5", size="512x512",
        )
        assert sdk.responses.create.called


class TestBackgroundCoercion:
    """gpt-image-2 rejects transparent — should coerce to opaque consistent with direct path."""

    def test_transparent_coerced_to_opaque_on_gpt_image_2(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        client.generate_image_via_responses(
            prompt="x", image_model="gpt-image-2",
            size="1024x1024", background="transparent",
        )
        tool = sdk.responses.create.call_args.kwargs["tools"][0]
        assert tool["background"] == "opaque"

    def test_transparent_preserved_for_gpt_image_1_5(self):
        client, sdk = _make_client_with_mock_response([_image_call()])
        client.generate_image_via_responses(
            prompt="x", image_model="gpt-image-1.5", background="transparent",
        )
        tool = sdk.responses.create.call_args.kwargs["tools"][0]
        assert tool["background"] == "transparent"


class TestResponseParsing:
    """Response output items parsed correctly into images/revised_prompt/reasoning_summary."""

    def test_single_image_call_returns_one_image(self):
        client, _ = _make_client_with_mock_response([
            _image_call(result="AAAA", revised="a revised prompt"),
            _message_item(),
        ])
        result = client.generate_image_via_responses(
            prompt="x", image_model="gpt-image-2", size="1024x1024",
        )
        assert result["images"] == ["AAAA"]
        assert "a revised prompt" in result["revised_prompt"]
        assert result["reasoning_summary"] == ""

    def test_multiple_image_calls_collected(self):
        client, _ = _make_client_with_mock_response([
            _image_call(result="IMG1"),
            _image_call(result="IMG2"),
            _message_item(),
        ])
        result = client.generate_image_via_responses(
            prompt="x", image_model="gpt-image-2", size="1024x1024",
        )
        assert result["images"] == ["IMG1", "IMG2"]

    def test_reasoning_summary_extracted(self):
        client, _ = _make_client_with_mock_response([
            _reasoning_item(text="I considered multiple options..."),
            _image_call(result="IMG"),
            _message_item(),
        ])
        result = client.generate_image_via_responses(
            prompt="x", image_model="gpt-image-2",
            size="1024x1024", reasoning_effort="medium",
        )
        assert "considered multiple options" in result["reasoning_summary"]

    def test_empty_output_returns_empty_images(self):
        client, _ = _make_client_with_mock_response([])
        result = client.generate_image_via_responses(
            prompt="x", image_model="gpt-image-2", size="1024x1024",
        )
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
        assert "gpt-5.4" in inp.options
        assert inp.default == "gpt-5.4"

    def test_has_image_model_input(self, schema):
        inp = next((i for i in schema.inputs if i.id == "image_model"), None)
        assert inp is not None
        assert "gpt-image-2" in inp.options
        assert inp.default == "gpt-image-2"

    def test_has_reasoning_effort_input(self, schema):
        inp = next((i for i in schema.inputs if i.id == "reasoning_effort"), None)
        assert inp is not None
        for level in ("none", "minimal", "low", "medium", "high", "xhigh"):
            assert level in inp.options
        assert inp.default == "none"

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
