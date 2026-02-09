# ABOUTME: Tests for ClaudeToolDefinition node — schema building, chaining, and validation.
# ABOUTME: Pure logic tests with no API mocking required.

import pytest
import json


class TestSingleToolCreation:
    """A valid tool_name + description + parameters_json produces a correct tool dict."""

    def test_single_tool_creation(self):
        from claude.tool_definition import ClaudeToolDefinition

        node = ClaudeToolDefinition()
        schema = json.dumps({
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        })

        (tools,) = node.build_tool(
            tool_name="extract_person",
            description="Extract person info from text",
            parameters_json=schema,
        )

        assert len(tools) == 1
        tool = tools[0]
        assert tool["name"] == "extract_person"
        assert tool["description"] == "Extract person info from text"
        assert tool["input_schema"]["type"] == "object"
        assert "name" in tool["input_schema"]["properties"]

    def test_input_types_structure(self):
        from claude.tool_definition import ClaudeToolDefinition

        input_types = ClaudeToolDefinition.INPUT_TYPES()
        assert "tool_name" in input_types["required"]
        assert "description" in input_types["required"]
        assert "parameters_json" in input_types["required"]
        assert "previous_tools" in input_types["optional"]
        assert input_types["optional"]["previous_tools"][0] == "CLAUDE_TOOLS"

    def test_return_type_is_claude_tools(self):
        from claude.tool_definition import ClaudeToolDefinition

        assert ClaudeToolDefinition.RETURN_TYPES == ("CLAUDE_TOOLS",)
        assert ClaudeToolDefinition.RETURN_NAMES == ("tools",)

    def test_category(self):
        from claude.tool_definition import ClaudeToolDefinition

        assert ClaudeToolDefinition.CATEGORY == "ERPK/Claude/Tools"


class TestToolChaining:
    """previous_tools input appends to the chain without mutating the original."""

    def test_tool_chaining(self):
        from claude.tool_definition import ClaudeToolDefinition

        node = ClaudeToolDefinition()
        schema_a = json.dumps({"type": "object", "properties": {"x": {"type": "string"}}})
        schema_b = json.dumps({"type": "object", "properties": {"y": {"type": "integer"}}})

        (first_tools,) = node.build_tool(
            tool_name="tool_a",
            description="First tool",
            parameters_json=schema_a,
        )

        (chained_tools,) = node.build_tool(
            tool_name="tool_b",
            description="Second tool",
            parameters_json=schema_b,
            previous_tools=first_tools,
        )

        assert len(chained_tools) == 2
        assert chained_tools[0]["name"] == "tool_a"
        assert chained_tools[1]["name"] == "tool_b"

    def test_chaining_does_not_mutate_original(self):
        from claude.tool_definition import ClaudeToolDefinition

        node = ClaudeToolDefinition()
        schema = json.dumps({"type": "object", "properties": {}})

        (original,) = node.build_tool(
            tool_name="first",
            description="First",
            parameters_json=schema,
        )
        original_len = len(original)

        node.build_tool(
            tool_name="second",
            description="Second",
            parameters_json=schema,
            previous_tools=original,
        )

        assert len(original) == original_len, "Chaining should not mutate the input list"


class TestValidation:
    """Invalid inputs raise ValueError with descriptive messages."""

    def test_invalid_json_raises(self):
        from claude.tool_definition import ClaudeToolDefinition

        node = ClaudeToolDefinition()
        with pytest.raises(ValueError, match="Invalid JSON"):
            node.build_tool(
                tool_name="test_tool",
                description="A tool",
                parameters_json="not valid json {{{",
            )

    def test_empty_name_raises(self):
        from claude.tool_definition import ClaudeToolDefinition

        node = ClaudeToolDefinition()
        schema = json.dumps({"type": "object", "properties": {}})

        with pytest.raises(ValueError, match="[Tt]ool name"):
            node.build_tool(
                tool_name="",
                description="A tool",
                parameters_json=schema,
            )

    def test_whitespace_only_name_raises(self):
        from claude.tool_definition import ClaudeToolDefinition

        node = ClaudeToolDefinition()
        schema = json.dumps({"type": "object", "properties": {}})

        with pytest.raises(ValueError, match="[Tt]ool name"):
            node.build_tool(
                tool_name="   ",
                description="A tool",
                parameters_json=schema,
            )

    def test_missing_type_field_raises(self):
        from claude.tool_definition import ClaudeToolDefinition

        node = ClaudeToolDefinition()
        with pytest.raises(ValueError, match="type"):
            node.build_tool(
                tool_name="test_tool",
                description="A tool",
                parameters_json=json.dumps({"properties": {"x": {"type": "string"}}}),
            )


class TestDuplicateNames:
    """When chaining produces a duplicate tool name, the earlier definition is replaced."""

    def test_duplicate_name_replaces(self):
        from claude.tool_definition import ClaudeToolDefinition

        node = ClaudeToolDefinition()
        schema_v1 = json.dumps({"type": "object", "properties": {"old": {"type": "string"}}})
        schema_v2 = json.dumps({"type": "object", "properties": {"new": {"type": "integer"}}})

        (first,) = node.build_tool(
            tool_name="extract",
            description="Version 1",
            parameters_json=schema_v1,
        )

        (result,) = node.build_tool(
            tool_name="extract",
            description="Version 2",
            parameters_json=schema_v2,
            previous_tools=first,
        )

        assert len(result) == 1, "Duplicate name should replace, not append"
        assert result[0]["description"] == "Version 2"
        assert "new" in result[0]["input_schema"]["properties"]
