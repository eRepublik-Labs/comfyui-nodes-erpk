# ABOUTME: Tests for ClaudeToolDefinition node — schema building, chaining, and validation.
# ABOUTME: Pure logic tests with no API mocking required.

import pytest
import json


class TestSingleToolCreation:
    """A valid tool_name + description + parameters_json produces a correct tool dict."""

    def test_single_tool_creation(self):
        from claude.tool_definition import ClaudeToolDefinition

        schema = json.dumps({
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        })

        result = ClaudeToolDefinition.execute(
            tool_name="extract_person",
            description="Extract person info from text",
            parameters_json=schema,
        )

        tools = result[0]
        assert len(tools) == 1
        tool = tools[0]
        assert tool["name"] == "extract_person"
        assert tool["description"] == "Extract person info from text"
        assert tool["input_schema"]["type"] == "object"
        assert "name" in tool["input_schema"]["properties"]

    def test_schema_structure(self):
        from claude.tool_definition import ClaudeToolDefinition

        schema = ClaudeToolDefinition.define_schema()
        input_ids = [i.id for i in schema.inputs]
        assert "tool_name" in input_ids
        assert "description" in input_ids
        assert "parameters_json" in input_ids
        assert "previous_tools" in input_ids
        prev = [i for i in schema.inputs if i.id == "previous_tools"][0]
        assert prev.io_type == "CLAUDE_TOOLS"

    def test_output_type_is_claude_tools(self):
        from claude.tool_definition import ClaudeToolDefinition

        schema = ClaudeToolDefinition.define_schema()
        assert len(schema.outputs) == 1
        assert schema.outputs[0].io_type == "CLAUDE_TOOLS"

    def test_category(self):
        from claude.tool_definition import ClaudeToolDefinition

        schema = ClaudeToolDefinition.define_schema()
        assert schema.category == "ERPK/Claude/Tools"


class TestToolChaining:
    """previous_tools input appends to the chain without mutating the original."""

    def test_tool_chaining(self):
        from claude.tool_definition import ClaudeToolDefinition

        schema_a = json.dumps({"type": "object", "properties": {"x": {"type": "string"}}})
        schema_b = json.dumps({"type": "object", "properties": {"y": {"type": "integer"}}})

        result_a = ClaudeToolDefinition.execute(
            tool_name="tool_a",
            description="First tool",
            parameters_json=schema_a,
        )

        result_b = ClaudeToolDefinition.execute(
            tool_name="tool_b",
            description="Second tool",
            parameters_json=schema_b,
            previous_tools=result_a[0],
        )

        chained_tools = result_b[0]
        assert len(chained_tools) == 2
        assert chained_tools[0]["name"] == "tool_a"
        assert chained_tools[1]["name"] == "tool_b"

    def test_chaining_does_not_mutate_original(self):
        from claude.tool_definition import ClaudeToolDefinition

        schema = json.dumps({"type": "object", "properties": {}})

        result_a = ClaudeToolDefinition.execute(
            tool_name="first",
            description="First",
            parameters_json=schema,
        )
        original = result_a[0]
        original_len = len(original)

        ClaudeToolDefinition.execute(
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

        with pytest.raises(ValueError, match="Invalid JSON"):
            ClaudeToolDefinition.execute(
                tool_name="test_tool",
                description="A tool",
                parameters_json="not valid json {{{",
            )

    def test_empty_name_raises(self):
        from claude.tool_definition import ClaudeToolDefinition

        schema = json.dumps({"type": "object", "properties": {}})

        with pytest.raises(ValueError, match="[Tt]ool name"):
            ClaudeToolDefinition.execute(
                tool_name="",
                description="A tool",
                parameters_json=schema,
            )

    def test_whitespace_only_name_raises(self):
        from claude.tool_definition import ClaudeToolDefinition

        schema = json.dumps({"type": "object", "properties": {}})

        with pytest.raises(ValueError, match="[Tt]ool name"):
            ClaudeToolDefinition.execute(
                tool_name="   ",
                description="A tool",
                parameters_json=schema,
            )

    def test_missing_type_field_raises(self):
        from claude.tool_definition import ClaudeToolDefinition

        with pytest.raises(ValueError, match="type"):
            ClaudeToolDefinition.execute(
                tool_name="test_tool",
                description="A tool",
                parameters_json=json.dumps({"properties": {"x": {"type": "string"}}}),
            )


class TestDuplicateNames:
    """When chaining produces a duplicate tool name, the earlier definition is replaced."""

    def test_duplicate_name_replaces(self):
        from claude.tool_definition import ClaudeToolDefinition

        schema_v1 = json.dumps({"type": "object", "properties": {"old": {"type": "string"}}})
        schema_v2 = json.dumps({"type": "object", "properties": {"new": {"type": "integer"}}})

        result_a = ClaudeToolDefinition.execute(
            tool_name="extract",
            description="Version 1",
            parameters_json=schema_v1,
        )

        result_b = ClaudeToolDefinition.execute(
            tool_name="extract",
            description="Version 2",
            parameters_json=schema_v2,
            previous_tools=result_a[0],
        )

        tools = result_b[0]
        assert len(tools) == 1, "Duplicate name should replace, not append"
        assert tools[0]["description"] == "Version 2"
        assert "new" in tools[0]["input_schema"]["properties"]
