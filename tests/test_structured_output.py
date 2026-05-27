# ABOUTME: Tests for ClaudeStructuredOutput node — JSON extraction from forced tool use.
# ABOUTME: Uses mocked API responses to test extraction logic without real API calls.

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, Mock


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

        client = Mock()
        tool_data = {"name": "Alice", "age": 30}
        client.send_request = AsyncMock(return_value=_make_response(
            [_make_tool_use_block("extract", tool_data)]
        ))

        result = asyncio.run(ClaudeStructuredOutput.execute(
            client=client,
            prompt="Extract the person info",
            tool=_make_tool_list("extract"),
        ))

        parsed = json.loads(result[0])
        assert parsed == {"name": "Alice", "age": 30}

    def test_extracts_thinking_text(self):
        from claude.structured_output import ClaudeStructuredOutput

        client = Mock()
        client.send_request = AsyncMock(return_value=_make_response([
            _make_text_block("Let me analyze this..."),
            _make_text_block("The text mentions a person."),
            _make_tool_use_block("extract", {"name": "Bob"}),
        ]))

        result = asyncio.run(ClaudeStructuredOutput.execute(
            client=client,
            prompt="Extract person",
            tool=_make_tool_list("extract"),
        ))

        thinking = result[1]
        assert "Let me analyze this..." in thinking
        assert "The text mentions a person." in thinking

    def test_passes_tools_and_tool_choice_to_client(self):
        from claude.structured_output import ClaudeStructuredOutput

        client = Mock()
        client.send_request = AsyncMock(return_value=_make_response(
            [_make_tool_use_block("extract", {"x": 1})]
        ))
        tools = _make_tool_list("extract")

        asyncio.run(ClaudeStructuredOutput.execute(
            client=client, prompt="Test prompt", tool=tools
        ))

        call_kwargs = client.send_request.call_args
        assert call_kwargs.kwargs["tools"] == tools
        assert call_kwargs.kwargs["tool_choice"] == {"type": "tool", "name": "extract"}

    def test_passes_optional_parameters(self):
        from claude.structured_output import ClaudeStructuredOutput

        client = Mock()
        client.send_request = AsyncMock(return_value=_make_response(
            [_make_tool_use_block("extract", {"x": 1})]
        ))

        asyncio.run(ClaudeStructuredOutput.execute(
            client=client,
            prompt="Test",
            tool=_make_tool_list("extract"),
            system_prompt="You are a parser",
            temperature=0.2,
            max_tokens=2048,
        ))

        call_kwargs = client.send_request.call_args.kwargs
        assert call_kwargs["system"] == "You are a parser"
        assert call_kwargs["temperature"] == 0.2
        assert call_kwargs["max_tokens"] == 2048

    def test_empty_thinking_when_no_text_blocks(self):
        from claude.structured_output import ClaudeStructuredOutput

        client = Mock()
        client.send_request = AsyncMock(return_value=_make_response(
            [_make_tool_use_block("extract", {"result": True})]
        ))

        result = asyncio.run(ClaudeStructuredOutput.execute(
            client=client,
            prompt="Test",
            tool=_make_tool_list("extract"),
        ))

        assert result[1] == ""


class TestStructuredOutputValidation:
    """Input validation catches bad configurations before hitting the API."""

    def test_rejects_multiple_tools(self):
        from claude.structured_output import ClaudeStructuredOutput

        client = Mock()
        two_tools = _make_tool_list("tool_a") + _make_tool_list("tool_b")

        with pytest.raises(ValueError, match="exactly 1 tool"):
            asyncio.run(ClaudeStructuredOutput.execute(
                client=client, prompt="Test", tool=two_tools
            ))

        client.send_request.assert_not_called()

    def test_rejects_empty_tools(self):
        from claude.structured_output import ClaudeStructuredOutput

        client = Mock()

        with pytest.raises(ValueError, match="exactly 1 tool"):
            asyncio.run(ClaudeStructuredOutput.execute(
                client=client, prompt="Test", tool=[]
            ))

        client.send_request.assert_not_called()

    def test_rejects_empty_prompt(self):
        from claude.structured_output import ClaudeStructuredOutput

        client = Mock()

        with pytest.raises(ValueError, match="[Pp]rompt"):
            asyncio.run(ClaudeStructuredOutput.execute(
                client=client, prompt="", tool=_make_tool_list()
            ))

        client.send_request.assert_not_called()

    def test_rejects_whitespace_prompt(self):
        from claude.structured_output import ClaudeStructuredOutput

        client = Mock()

        with pytest.raises(ValueError, match="[Pp]rompt"):
            asyncio.run(ClaudeStructuredOutput.execute(
                client=client, prompt="   \n  ", tool=_make_tool_list()
            ))


class TestStructuredOutputErrors:
    """API errors propagate cleanly to ComfyUI's error handling."""

    def test_propagates_api_errors(self):
        from claude.structured_output import ClaudeStructuredOutput

        client = Mock()
        client.send_request = AsyncMock(side_effect=Exception("API connection failed"))

        with pytest.raises(Exception, match="API connection failed"):
            asyncio.run(ClaudeStructuredOutput.execute(
                client=client,
                prompt="Test prompt",
                tool=_make_tool_list(),
            ))


class TestStructuredOutputNodeMeta:
    """Verify the V3 node contract (schema, inputs, outputs)."""

    def test_schema_structure(self):
        from claude.structured_output import ClaudeStructuredOutput

        schema = ClaudeStructuredOutput.define_schema()
        input_ids = [i.id for i in schema.inputs]
        assert "prompt" in input_ids
        assert "tool" in input_ids
        tool_input = [i for i in schema.inputs if i.id == "tool"][0]
        assert tool_input.io_type == "CLAUDE_TOOLS"
        assert "client" in input_ids
        client_input = [i for i in schema.inputs if i.id == "client"][0]
        assert client_input.io_type == "CLAUDE_API_CLIENT"

    def test_output_types(self):
        from claude.structured_output import ClaudeStructuredOutput

        schema = ClaudeStructuredOutput.define_schema()
        assert len(schema.outputs) == 2
        assert schema.outputs[0].io_type == "STRING"
        assert schema.outputs[1].io_type == "STRING"

    def test_category(self):
        from claude.structured_output import ClaudeStructuredOutput

        schema = ClaudeStructuredOutput.define_schema()
        assert schema.category == "ERPK/Claude/Tools"

    def test_not_idempotent(self):
        from claude.structured_output import ClaudeStructuredOutput

        schema = ClaudeStructuredOutput.define_schema()
        assert schema.not_idempotent is True
