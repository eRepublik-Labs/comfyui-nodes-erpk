# ABOUTME: Tests for V3 ConcatenateStrings node schema and execution.
# ABOUTME: Validates define_schema, execute classmethod, and string concatenation logic.

"""
Tests for the V3 ConcatenateStrings node.

Validates:
- Node inherits from IO.ComfyNode
- define_schema returns correct IO.Schema
- execute is a classmethod and produces correct output
- Input/output types match expected V3 patterns
"""

import pytest

IO = pytest.importorskip("comfy_api.latest").IO


class TestConcatenateStringsSchema:
    """Test V3 schema structure for ConcatenateStrings."""

    @pytest.fixture
    def node_class(self):
        from utils.concat_strings import ConcatenateStrings
        return ConcatenateStrings

    @pytest.fixture
    def schema(self, node_class):
        return node_class.define_schema()

    def test_inherits_comfy_node(self, node_class):
        """Node class must inherit from IO.ComfyNode."""
        assert issubclass(node_class, IO.ComfyNode)

    def test_has_define_schema(self, node_class):
        """Must have define_schema classmethod."""
        assert hasattr(node_class, "define_schema")
        assert isinstance(
            node_class.__dict__.get("define_schema"),
            classmethod,
        )

    def test_schema_node_id(self, schema):
        """node_id must match the V1 mapping key for workflow compatibility."""
        assert schema.node_id == "ERPK_ConcatenateStrings"

    def test_schema_display_name(self, schema):
        """display_name should be user-friendly."""
        assert schema.display_name == "Concatenate Strings (ERPK)"

    def test_schema_category(self, schema):
        assert schema.category == "ERPK/utils"

    def test_schema_has_description(self, schema):
        assert schema.description
        assert "Concatenate" in schema.description

    def test_schema_has_string_output(self, schema):
        """Should output a single STRING."""
        outputs = schema.outputs
        assert len(outputs) == 1
        assert outputs[0].io_type == "STRING"

    def test_schema_has_delimiter_input(self, schema):
        """Should have a Delimiter string input with newline default."""
        delimiter = _find_input(schema, "Delimiter")
        assert delimiter is not None
        assert delimiter.io_type == "STRING"
        assert delimiter.default == "\\n"

    def test_schema_has_include_labels_input(self, schema):
        """Should have an Include Labels boolean input."""
        inc = _find_input(schema, "Include Labels")
        assert inc is not None
        assert inc.io_type == "BOOLEAN"
        assert inc.default is False

    def test_schema_has_label_on_same_line_input(self, schema):
        """Should have a Label on Same Line boolean input."""
        lsl = _find_input(schema, "Label on Same Line")
        assert lsl is not None
        assert lsl.io_type == "BOOLEAN"
        assert lsl.default is True

    def test_schema_has_10_text_inputs(self, schema):
        """Should have Text 1 through Text 10."""
        for i in range(1, 11):
            txt = _find_input(schema, f"Text {i}")
            assert txt is not None, f"Missing Text {i}"
            assert txt.io_type == "STRING"

    def test_schema_has_10_label_inputs(self, schema):
        """Should have Label 1 through Label 10."""
        for i in range(1, 11):
            lbl = _find_input(schema, f"Label {i}")
            assert lbl is not None, f"Missing Label {i}"
            assert lbl.io_type == "STRING"

    def test_all_text_inputs_are_optional(self, schema):
        """All text/label inputs should be optional."""
        for i in range(1, 11):
            txt = _find_input(schema, f"Text {i}")
            assert txt.optional is True, f"Text {i} should be optional"
            lbl = _find_input(schema, f"Label {i}")
            assert lbl.optional is True, f"Label {i} should be optional"

    def test_text_inputs_are_multiline(self, schema):
        """Text inputs should be multiline."""
        for i in range(1, 11):
            txt = _find_input(schema, f"Text {i}")
            assert txt.multiline is True, f"Text {i} should be multiline"

    def test_label_inputs_are_singleline(self, schema):
        """Label inputs should be singleline."""
        for i in range(1, 11):
            lbl = _find_input(schema, f"Label {i}")
            assert lbl.multiline is not True, f"Label {i} should be singleline"


class TestConcatenateStringsExecute:
    """Test V3 execute method behavior."""

    @pytest.fixture
    def node_class(self):
        from utils.concat_strings import ConcatenateStrings
        return ConcatenateStrings

    def test_execute_is_classmethod(self, node_class):
        assert isinstance(
            node_class.__dict__.get("execute"),
            classmethod,
        )

    def test_basic_concatenation(self, node_class):
        """Two texts joined with newline delimiter."""
        result = node_class.execute(**{
            "Delimiter": "\\n",
            "Include Labels": False,
            "Label on Same Line": True,
            "Text 1": "hello",
            "Text 2": "world",
        })
        assert result[0] == "hello\nworld"

    def test_custom_delimiter(self, node_class):
        result = node_class.execute(**{
            "Delimiter": ", ",
            "Include Labels": False,
            "Label on Same Line": True,
            "Text 1": "a",
            "Text 2": "b",
            "Text 3": "c",
        })
        assert result[0] == "a, b, c"

    def test_with_labels_same_line(self, node_class):
        result = node_class.execute(**{
            "Delimiter": "\\n",
            "Include Labels": True,
            "Label on Same Line": True,
            "Label 1": "Name:",
            "Text 1": "Alice",
            "Label 2": "Age:",
            "Text 2": "30",
        })
        assert result[0] == "Name: Alice\nAge: 30"

    def test_with_labels_separate_line(self, node_class):
        result = node_class.execute(**{
            "Delimiter": "\\n\\n",
            "Include Labels": True,
            "Label on Same Line": False,
            "Label 1": "Header",
            "Text 1": "Content",
        })
        assert result[0] == "Header\nContent"

    def test_skips_empty_text(self, node_class):
        result = node_class.execute(**{
            "Delimiter": ", ",
            "Include Labels": False,
            "Label on Same Line": True,
            "Text 1": "only",
            "Text 2": "",
            "Text 3": "these",
        })
        assert result[0] == "only, these"

    def test_returns_node_output(self, node_class):
        """V3 execute must return IO.NodeOutput."""
        result = node_class.execute(**{
            "Delimiter": " ",
            "Include Labels": False,
            "Label on Same Line": True,
            "Text 1": "test",
        })
        assert isinstance(result, IO.NodeOutput)

    def test_empty_inputs(self, node_class):
        """No text inputs should produce empty string."""
        result = node_class.execute(**{
            "Delimiter": "\\n",
            "Include Labels": False,
            "Label on Same Line": True,
        })
        assert result[0] == ""


def _find_input(schema, input_id: str):
    """Find an input by ID in a V3 schema."""
    for inp in schema.inputs:
        if inp.id == input_id:
            return inp
    return None
