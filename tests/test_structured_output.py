# ABOUTME: Tests for ClaudeStructuredOutput input validation, error propagation and schema contract.
# ABOUTME: The request/response behaviour is covered over the real SDK in test_claude_node_requests.py.

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock


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
