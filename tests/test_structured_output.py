# ABOUTME: Tests for ClaudeStructuredOutput node — JSON extraction from forced tool use.
# ABOUTME: Uses mocked API responses to test extraction logic without real API calls.

import json
import pytest
from unittest.mock import Mock, MagicMock


def _make_tool_use_block(name="extract", input_data=None):
    """Create a mock ToolUseBlock."""
    block = Mock()
    block.type = "tool_use"
    block.id = "toolu_test123"
    block.name = name
    block.input = input_data or {"key": "value"}
    return block


def _make_text_block(text="Thinking about the request..."):
    """Create a mock TextBlock."""
    block = Mock()
    block.type = "text"
    block.text = text
    return block


def _make_response(content_blocks, stop_reason="tool_use"):
    """Create a mock API response."""
    response = Mock()
    response.content = content_blocks
    response.stop_reason = stop_reason
    response.usage = Mock(
        input_tokens=100,
        output_tokens=50,
        cache_read_input_tokens=0,
        cache_creation_input_tokens=0,
    )
    return response


def _make_tool_list(name="extract"):
    """Create a single-element CLAUDE_TOOLS list."""
    return [
        {
            "name": name,
            "description": "Extract structured data",
            "input_schema": {
                "type": "object",
                "properties": {"key": {"type": "string"}},
            },
        }
    ]


class TestStructuredOutputExtraction:
    """Happy-path tests for JSON extraction from forced tool use responses."""

    def test_extracts_json_from_tool_use_response(self):
        from claude.structured_output import ClaudeStructuredOutput

        node = ClaudeStructuredOutput()
        client = Mock()
        tool_data = {"name": "Alice", "age": 30}
        client.send_request.return_value = _make_response(
            [_make_tool_use_block("extract", tool_data)]
        )

        (json_output, thinking) = node.extract(
            client=client,
            prompt="Extract the person info",
            tool=_make_tool_list("extract"),
        )

        parsed = json.loads(json_output)
        assert parsed == {"name": "Alice", "age": 30}

    def test_extracts_thinking_text(self):
        from claude.structured_output import ClaudeStructuredOutput

        node = ClaudeStructuredOutput()
        client = Mock()
        client.send_request.return_value = _make_response([
            _make_text_block("Let me analyze this..."),
            _make_text_block("The text mentions a person."),
            _make_tool_use_block("extract", {"name": "Bob"}),
        ])

        (json_output, thinking) = node.extract(
            client=client,
            prompt="Extract person",
            tool=_make_tool_list("extract"),
        )

        assert "Let me analyze this..." in thinking
        assert "The text mentions a person." in thinking

    def test_passes_tools_and_tool_choice_to_client(self):
        from claude.structured_output import ClaudeStructuredOutput

        node = ClaudeStructuredOutput()
        client = Mock()
        client.send_request.return_value = _make_response(
            [_make_tool_use_block("extract", {"x": 1})]
        )
        tools = _make_tool_list("extract")

        node.extract(client=client, prompt="Test prompt", tool=tools)

        call_kwargs = client.send_request.call_args
        assert call_kwargs.kwargs["tools"] == tools
        assert call_kwargs.kwargs["tool_choice"] == {"type": "tool", "name": "extract"}

    def test_passes_optional_parameters(self):
        from claude.structured_output import ClaudeStructuredOutput

        node = ClaudeStructuredOutput()
        client = Mock()
        client.send_request.return_value = _make_response(
            [_make_tool_use_block("extract", {"x": 1})]
        )

        node.extract(
            client=client,
            prompt="Test",
            tool=_make_tool_list("extract"),
            system_prompt="You are a parser",
            temperature=0.2,
            max_tokens=2048,
        )

        call_kwargs = client.send_request.call_args.kwargs
        assert call_kwargs["system"] == "You are a parser"
        assert call_kwargs["temperature"] == 0.2
        assert call_kwargs["max_tokens"] == 2048

    def test_empty_thinking_when_no_text_blocks(self):
        from claude.structured_output import ClaudeStructuredOutput

        node = ClaudeStructuredOutput()
        client = Mock()
        client.send_request.return_value = _make_response(
            [_make_tool_use_block("extract", {"result": True})]
        )

        (json_output, thinking) = node.extract(
            client=client,
            prompt="Test",
            tool=_make_tool_list("extract"),
        )

        assert thinking == ""


class TestStructuredOutputValidation:
    """Input validation catches bad configurations before hitting the API."""

    def test_rejects_multiple_tools(self):
        from claude.structured_output import ClaudeStructuredOutput

        node = ClaudeStructuredOutput()
        client = Mock()
        two_tools = _make_tool_list("tool_a") + _make_tool_list("tool_b")

        with pytest.raises(ValueError, match="exactly 1 tool"):
            node.extract(client=client, prompt="Test", tool=two_tools)

        client.send_request.assert_not_called()

    def test_rejects_empty_tools(self):
        from claude.structured_output import ClaudeStructuredOutput

        node = ClaudeStructuredOutput()
        client = Mock()

        with pytest.raises(ValueError, match="exactly 1 tool"):
            node.extract(client=client, prompt="Test", tool=[])

        client.send_request.assert_not_called()

    def test_rejects_empty_prompt(self):
        from claude.structured_output import ClaudeStructuredOutput

        node = ClaudeStructuredOutput()
        client = Mock()

        with pytest.raises(ValueError, match="[Pp]rompt"):
            node.extract(client=client, prompt="", tool=_make_tool_list())

        client.send_request.assert_not_called()

    def test_rejects_whitespace_prompt(self):
        from claude.structured_output import ClaudeStructuredOutput

        node = ClaudeStructuredOutput()
        client = Mock()

        with pytest.raises(ValueError, match="[Pp]rompt"):
            node.extract(client=client, prompt="   \n  ", tool=_make_tool_list())


class TestStructuredOutputErrors:
    """API errors propagate cleanly to ComfyUI's error handling."""

    def test_propagates_api_errors(self):
        from claude.structured_output import ClaudeStructuredOutput

        node = ClaudeStructuredOutput()
        client = Mock()
        client.send_request.side_effect = Exception("API connection failed")

        with pytest.raises(Exception, match="API connection failed"):
            node.extract(
                client=client,
                prompt="Test prompt",
                tool=_make_tool_list(),
            )


class TestStructuredOutputNodeMeta:
    """Verify the ComfyUI node contract (INPUT_TYPES, RETURN_TYPES, etc.)."""

    def test_input_types_structure(self):
        from claude.structured_output import ClaudeStructuredOutput

        input_types = ClaudeStructuredOutput.INPUT_TYPES()
        assert "prompt" in input_types["required"]
        assert "tool" in input_types["required"]
        assert input_types["required"]["tool"][0] == "CLAUDE_TOOLS"
        assert "client" in input_types["optional"]
        assert input_types["optional"]["client"][0] == "CLAUDE_API_CLIENT"

    def test_return_types(self):
        from claude.structured_output import ClaudeStructuredOutput

        assert ClaudeStructuredOutput.RETURN_TYPES == ("STRING", "STRING")
        assert ClaudeStructuredOutput.RETURN_NAMES == ("json_output", "thinking")

    def test_category(self):
        from claude.structured_output import ClaudeStructuredOutput

        assert ClaudeStructuredOutput.CATEGORY == "ERPK/Claude/Tools"

    def test_is_changed_disables_caching(self):
        from claude.structured_output import ClaudeStructuredOutput
        import math

        result = ClaudeStructuredOutput.IS_CHANGED()
        assert math.isnan(result)
