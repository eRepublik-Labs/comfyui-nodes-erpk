# ABOUTME: V3 structural and behavioral tests for all Claude provider nodes.
# ABOUTME: Validates V3 compliance, custom types, schema fields, and pure-logic execute paths.

"""
V3 tests for Claude provider nodes (10 nodes total).

Validates:
- All classes inherit from IO.ComfyNode
- define_schema returns correct Schema with expected fields
- execute is a @classmethod
- Custom types (CLAUDE_API_CLIENT, CLAUDE_CONVERSATION, CLAUDE_TOOLS) in schemas
- not_idempotent and is_output_node flags match V1 behavior
- Pure-logic execute paths (ToolDefinition) produce correct NodeOutput
"""

import inspect
import json
import pytest

IO = pytest.importorskip("comfy_api.latest").IO


def _import_node(module_name, class_name):
    """Import a node class from the claude package."""
    import importlib
    mod = importlib.import_module(f"claude.{module_name}")
    return getattr(mod, class_name)


# --- Parametrized structural data for all 10 nodes ---
# (module, class_name, node_id, display_name, category, not_idempotent, is_output_node)
CLAUDE_NODES = [
    ("nodes", "ClaudeAPIClient", "ClaudeAPIClient",
     "Claude API Client", "ERPK/Claude", False, False),
    ("nodes", "ClaudeUsageStats", "ClaudeUsageStats",
     "Claude Usage Stats", "ERPK/Claude", False, True),
    ("text_generation", "ClaudeTextGeneration", "ClaudeTextGeneration",
     "Claude Text Generation", "ERPK/Claude", True, False),
    ("prompt_enhancer", "ClaudePromptEnhancer", "ClaudePromptEnhancer",
     "Claude Prompt Enhancer", "ERPK/Claude", True, False),
    ("vision_analysis", "ClaudeVisionAnalysis", "ClaudeVisionAnalysis",
     "Claude Vision Analysis", "ERPK/Claude", True, False),
    ("conversation", "ClaudeConversation", "ClaudeConversation",
     "Claude Conversation", "ERPK/Claude", True, False),
    ("conversation", "ClaudeConversationInfo", "ClaudeConversationInfo",
     "Claude Conversation Info", "ERPK/Claude", False, True),
    ("token_counter", "ClaudeTokenCounter", "ClaudeTokenCounter",
     "Claude Token Counter", "ERPK/Claude", False, True),
    ("tool_definition", "ClaudeToolDefinition", "ClaudeToolDefinition",
     "Claude Tool Definition", "ERPK/Claude/Tools", False, False),
    ("structured_output", "ClaudeStructuredOutput", "ClaudeStructuredOutput",
     "Claude Structured Output", "ERPK/Claude/Tools", True, False),
]


@pytest.fixture(params=CLAUDE_NODES, ids=[n[2] for n in CLAUDE_NODES])
def node_spec(request):
    """Yield (cls, node_id, display_name, category, not_idempotent, is_output_node)."""
    module, class_name, node_id, display_name, category, not_idempotent, is_output_node = request.param
    cls = _import_node(module, class_name)
    return cls, node_id, display_name, category, not_idempotent, is_output_node


class TestClaudeV3Compliance:
    """All Claude nodes comply with V3 API requirements."""

    def test_inherits_comfy_node(self, node_spec):
        cls, *_ = node_spec
        assert issubclass(cls, IO.ComfyNode), f"{cls.__name__} must inherit IO.ComfyNode"

    def test_has_define_schema(self, node_spec):
        cls, *_ = node_spec
        assert hasattr(cls, "define_schema")
        assert callable(cls.define_schema)

    def test_has_execute(self, node_spec):
        cls, *_ = node_spec
        assert hasattr(cls, "execute")
        assert callable(cls.execute)

    def test_execute_is_classmethod(self, node_spec):
        cls, *_ = node_spec
        assert isinstance(inspect.getattr_static(cls, "execute"), classmethod), \
            f"{cls.__name__}.execute must be a @classmethod"

    def test_schema_node_id(self, node_spec):
        cls, node_id, *_ = node_spec
        schema = cls.define_schema()
        assert schema.node_id == node_id

    def test_schema_display_name(self, node_spec):
        cls, _, display_name, *_ = node_spec
        schema = cls.define_schema()
        assert schema.display_name == display_name

    def test_schema_category(self, node_spec):
        cls, _, _, category, *_ = node_spec
        schema = cls.define_schema()
        assert schema.category == category

    def test_schema_not_idempotent(self, node_spec):
        cls, _, _, _, not_idempotent, _ = node_spec
        schema = cls.define_schema()
        assert schema.not_idempotent == not_idempotent, \
            f"{cls.__name__}: expected not_idempotent={not_idempotent}"

    def test_schema_is_output_node(self, node_spec):
        cls, _, _, _, _, is_output_node = node_spec
        schema = cls.define_schema()
        assert schema.is_output_node == is_output_node, \
            f"{cls.__name__}: expected is_output_node={is_output_node}"

    def test_schema_has_inputs(self, node_spec):
        cls, *_ = node_spec
        schema = cls.define_schema()
        assert len(schema.inputs) > 0, f"{cls.__name__} schema must have inputs"

    def test_schema_has_outputs(self, node_spec):
        cls, *_ = node_spec
        schema = cls.define_schema()
        assert len(schema.outputs) > 0, f"{cls.__name__} schema must have outputs"


class TestClaudeCustomTypes:
    """Custom types appear correctly in schemas."""

    def test_api_client_outputs_custom_type(self):
        cls = _import_node("nodes", "ClaudeAPIClient")
        schema = cls.define_schema()
        output_types = [o.io_type for o in schema.outputs]
        assert "CLAUDE_API_CLIENT" in output_types

    def test_usage_stats_accepts_custom_client(self):
        cls = _import_node("nodes", "ClaudeUsageStats")
        schema = cls.define_schema()
        input_types = [i.io_type for i in schema.inputs]
        assert "CLAUDE_API_CLIENT" in input_types

    def test_text_gen_accepts_optional_client(self):
        cls = _import_node("text_generation", "ClaudeTextGeneration")
        schema = cls.define_schema()
        client_inputs = [i for i in schema.inputs if i.id == "client"]
        assert len(client_inputs) == 1
        assert client_inputs[0].optional is True
        assert client_inputs[0].io_type == "CLAUDE_API_CLIENT"

    def test_conversation_outputs_custom_type(self):
        cls = _import_node("conversation", "ClaudeConversation")
        schema = cls.define_schema()
        output_types = [o.io_type for o in schema.outputs]
        assert "CLAUDE_CONVERSATION" in output_types

    def test_conversation_accepts_custom_history(self):
        cls = _import_node("conversation", "ClaudeConversation")
        schema = cls.define_schema()
        input_types = [i.io_type for i in schema.inputs]
        assert "CLAUDE_CONVERSATION" in input_types

    def test_conversation_info_accepts_custom_history(self):
        cls = _import_node("conversation", "ClaudeConversationInfo")
        schema = cls.define_schema()
        input_types = [i.io_type for i in schema.inputs]
        assert "CLAUDE_CONVERSATION" in input_types

    def test_tool_definition_outputs_tools_type(self):
        cls = _import_node("tool_definition", "ClaudeToolDefinition")
        schema = cls.define_schema()
        output_types = [o.io_type for o in schema.outputs]
        assert "CLAUDE_TOOLS" in output_types

    def test_structured_output_accepts_tools_type(self):
        cls = _import_node("structured_output", "ClaudeStructuredOutput")
        schema = cls.define_schema()
        input_types = [i.io_type for i in schema.inputs]
        assert "CLAUDE_TOOLS" in input_types

    def test_vision_analysis_accepts_image(self):
        cls = _import_node("vision_analysis", "ClaudeVisionAnalysis")
        schema = cls.define_schema()
        input_types = [i.io_type for i in schema.inputs]
        assert "IMAGE" in input_types


class TestClaudeNoDuplicateIds:
    """No duplicate node_ids across all Claude nodes."""

    def test_no_duplicate_node_ids(self):
        ids = []
        for module, class_name, *_ in CLAUDE_NODES:
            cls = _import_node(module, class_name)
            schema = cls.define_schema()
            ids.append(schema.node_id)
        assert len(ids) == len(set(ids)), f"Duplicate node_ids: {ids}"


class TestClaudeProviderExport:
    """claude/__init__.py exports NODES list for ERPKExtension."""

    def test_nodes_list_exported(self):
        import importlib
        mod = importlib.import_module("claude")
        assert hasattr(mod, "NODES"), "claude package must export NODES"
        assert isinstance(mod.NODES, list)

    def test_nodes_list_has_all_classes(self):
        import importlib
        mod = importlib.import_module("claude")
        assert len(mod.NODES) == 10, f"Expected 10 Claude nodes, got {len(mod.NODES)}"

    def test_nodes_list_all_comfy_nodes(self):
        import importlib
        mod = importlib.import_module("claude")
        for cls in mod.NODES:
            assert issubclass(cls, IO.ComfyNode), \
                f"{cls.__name__} in NODES must inherit IO.ComfyNode"


class TestToolDefinitionBehavior:
    """Behavioral tests for ClaudeToolDefinition execute (pure logic, no API)."""

    def test_execute_builds_single_tool(self):
        cls = _import_node("tool_definition", "ClaudeToolDefinition")
        schema = json.dumps({
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        })
        result = cls.execute(
            tool_name="extract_person",
            description="Extract person info",
            parameters_json=schema,
        )
        assert isinstance(result, IO.NodeOutput)
        tools = result[0]
        assert len(tools) == 1
        assert tools[0]["name"] == "extract_person"
        assert tools[0]["description"] == "Extract person info"
        assert tools[0]["input_schema"]["type"] == "object"

    def test_execute_chains_tools(self):
        cls = _import_node("tool_definition", "ClaudeToolDefinition")
        schema_a = json.dumps({"type": "object", "properties": {}})
        schema_b = json.dumps({"type": "object", "properties": {}})

        result_a = cls.execute(
            tool_name="tool_a",
            description="First",
            parameters_json=schema_a,
        )
        result_b = cls.execute(
            tool_name="tool_b",
            description="Second",
            parameters_json=schema_b,
            previous_tools=result_a[0],
        )
        assert len(result_b[0]) == 2
        assert result_b[0][0]["name"] == "tool_a"
        assert result_b[0][1]["name"] == "tool_b"

    def test_execute_does_not_mutate_previous(self):
        cls = _import_node("tool_definition", "ClaudeToolDefinition")
        schema = json.dumps({"type": "object", "properties": {}})

        result_a = cls.execute(
            tool_name="first",
            description="First",
            parameters_json=schema,
        )
        original_tools = result_a[0]
        original_len = len(original_tools)

        cls.execute(
            tool_name="second",
            description="Second",
            parameters_json=schema,
            previous_tools=original_tools,
        )
        assert len(original_tools) == original_len, "Chaining must not mutate the input"

    def test_execute_validates_empty_name(self):
        cls = _import_node("tool_definition", "ClaudeToolDefinition")
        schema = json.dumps({"type": "object", "properties": {}})
        with pytest.raises(ValueError, match="[Tt]ool name"):
            cls.execute(
                tool_name="",
                description="A tool",
                parameters_json=schema,
            )

    def test_execute_validates_bad_json(self):
        cls = _import_node("tool_definition", "ClaudeToolDefinition")
        with pytest.raises(ValueError, match="Invalid JSON"):
            cls.execute(
                tool_name="test",
                description="A tool",
                parameters_json="not valid {{{",
            )

    def test_execute_validates_missing_type_field(self):
        cls = _import_node("tool_definition", "ClaudeToolDefinition")
        with pytest.raises(ValueError, match="type"):
            cls.execute(
                tool_name="test",
                description="A tool",
                parameters_json=json.dumps({"properties": {}}),
            )

    def test_execute_replaces_duplicate_name(self):
        cls = _import_node("tool_definition", "ClaudeToolDefinition")
        schema_v1 = json.dumps({"type": "object", "properties": {"old": {"type": "string"}}})
        schema_v2 = json.dumps({"type": "object", "properties": {"new": {"type": "integer"}}})

        result_a = cls.execute(
            tool_name="extract",
            description="Version 1",
            parameters_json=schema_v1,
        )
        result_b = cls.execute(
            tool_name="extract",
            description="Version 2",
            parameters_json=schema_v2,
            previous_tools=result_a[0],
        )
        tools = result_b[0]
        assert len(tools) == 1, "Duplicate name should replace, not append"
        assert tools[0]["description"] == "Version 2"
