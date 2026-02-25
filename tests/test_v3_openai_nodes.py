# ABOUTME: V3 structural and behavioral tests for all OpenAI provider nodes.
# ABOUTME: Validates V3 compliance, custom types, model COMBO lists, and provider export.

"""
V3 tests for OpenAI provider nodes (7 nodes total).

Validates:
- All classes inherit from IO.ComfyNode
- define_schema returns correct Schema with expected fields
- execute is a @classmethod
- Custom types (OPENAI_API_CLIENT, OPENAI_CHAT_SESSION) in schemas
- not_idempotent and is_output_node flags match V1 behavior
- Model COMBO options sourced from OpenAIClient constants
"""

import inspect
import pytest

IO = pytest.importorskip("comfy_api.latest").IO


def _import_node(module_name, class_name):
    """Import a node class from the openai package."""
    import importlib
    mod = importlib.import_module(f"openai.{module_name}")
    return getattr(mod, class_name)


# --- Parametrized structural data for all 7 nodes ---
# (module, class_name, node_id, display_name, category, not_idempotent, is_output_node)
OPENAI_NODES = [
    ("nodes", "OpenAIAPIConfig", "OpenAIAPIConfig",
     "OpenAI API Config", "ERPK/OpenAI", False, False),
    ("nodes", "OpenAITextGeneration", "OpenAITextGeneration",
     "OpenAI Text Generation", "ERPK/OpenAI", True, False),
    ("nodes", "OpenAIChat", "OpenAIChat",
     "OpenAI Chat", "ERPK/OpenAI", True, False),
    ("nodes", "OpenAIVision", "OpenAIVision",
     "OpenAI Vision", "ERPK/OpenAI", True, False),
    ("nodes", "OpenAISystemInstruction", "OpenAISystemInstruction",
     "OpenAI System Instruction", "ERPK/OpenAI", False, False),
    ("image_nodes", "OpenAIImageGeneration", "OpenAIImageGeneration",
     "OpenAI Image Generation", "ERPK/OpenAI", True, False),
    ("image_nodes", "OpenAIImageEdit", "OpenAIImageEdit",
     "OpenAI Image Edit", "ERPK/OpenAI", True, False),
]


@pytest.fixture(params=OPENAI_NODES, ids=[n[2] for n in OPENAI_NODES])
def node_spec(request):
    """Yield (cls, node_id, display_name, category, not_idempotent, is_output_node)."""
    module, class_name, node_id, display_name, category, not_idempotent, is_output_node = request.param
    cls = _import_node(module, class_name)
    return cls, node_id, display_name, category, not_idempotent, is_output_node


class TestOpenAIV3Compliance:
    """All OpenAI nodes comply with V3 API requirements."""

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


class TestOpenAICustomTypes:
    """Custom types appear correctly in schemas."""

    def test_api_config_outputs_client(self):
        cls = _import_node("nodes", "OpenAIAPIConfig")
        schema = cls.define_schema()
        output_types = [o.io_type for o in schema.outputs]
        assert "OPENAI_API_CLIENT" in output_types

    def test_system_instruction_accepts_client(self):
        cls = _import_node("nodes", "OpenAISystemInstruction")
        schema = cls.define_schema()
        input_types = [i.io_type for i in schema.inputs]
        assert "OPENAI_API_CLIENT" in input_types

    def test_system_instruction_outputs_client(self):
        cls = _import_node("nodes", "OpenAISystemInstruction")
        schema = cls.define_schema()
        output_types = [o.io_type for o in schema.outputs]
        assert "OPENAI_API_CLIENT" in output_types

    def test_text_gen_accepts_optional_client(self):
        cls = _import_node("nodes", "OpenAITextGeneration")
        schema = cls.define_schema()
        client_inputs = [i for i in schema.inputs if i.id == "client"]
        assert len(client_inputs) == 1
        assert client_inputs[0].optional is True
        assert client_inputs[0].io_type == "OPENAI_API_CLIENT"

    def test_chat_accepts_optional_client(self):
        cls = _import_node("nodes", "OpenAIChat")
        schema = cls.define_schema()
        client_inputs = [i for i in schema.inputs if i.id == "client"]
        assert len(client_inputs) == 1
        assert client_inputs[0].optional is True

    def test_chat_accepts_chat_session(self):
        cls = _import_node("nodes", "OpenAIChat")
        schema = cls.define_schema()
        input_types = [i.io_type for i in schema.inputs]
        assert "OPENAI_CHAT_SESSION" in input_types

    def test_chat_outputs_chat_session(self):
        cls = _import_node("nodes", "OpenAIChat")
        schema = cls.define_schema()
        output_types = [o.io_type for o in schema.outputs]
        assert "OPENAI_CHAT_SESSION" in output_types

    def test_vision_accepts_image(self):
        cls = _import_node("nodes", "OpenAIVision")
        schema = cls.define_schema()
        input_types = [i.io_type for i in schema.inputs]
        assert "IMAGE" in input_types

    def test_image_gen_outputs_image_and_revised_prompt(self):
        cls = _import_node("image_nodes", "OpenAIImageGeneration")
        schema = cls.define_schema()
        output_types = [o.io_type for o in schema.outputs]
        assert "IMAGE" in output_types
        assert "STRING" in output_types

    def test_image_edit_accepts_image_and_optional_mask(self):
        cls = _import_node("image_nodes", "OpenAIImageEdit")
        schema = cls.define_schema()
        input_types = [i.io_type for i in schema.inputs]
        assert "IMAGE" in input_types
        mask_inputs = [i for i in schema.inputs if i.id == "mask"]
        assert len(mask_inputs) == 1
        assert mask_inputs[0].optional is True
        assert mask_inputs[0].io_type == "MASK"

    def test_image_edit_outputs_image(self):
        cls = _import_node("image_nodes", "OpenAIImageEdit")
        schema = cls.define_schema()
        output_types = [o.io_type for o in schema.outputs]
        assert "IMAGE" in output_types

    def test_image_gen_accepts_optional_api_key(self):
        cls = _import_node("image_nodes", "OpenAIImageGeneration")
        schema = cls.define_schema()
        key_inputs = [i for i in schema.inputs if i.id == "api_key"]
        assert len(key_inputs) == 1
        assert key_inputs[0].optional is True

    def test_image_edit_accepts_optional_api_key(self):
        cls = _import_node("image_nodes", "OpenAIImageEdit")
        schema = cls.define_schema()
        key_inputs = [i for i in schema.inputs if i.id == "api_key"]
        assert len(key_inputs) == 1
        assert key_inputs[0].optional is True


class TestOpenAIModelOptions:
    """Model COMBO options are correctly sourced from OpenAIClient constants."""

    def test_text_gen_model_options(self):
        from openai.openai_api.client import OpenAIClient
        cls = _import_node("nodes", "OpenAITextGeneration")
        schema = cls.define_schema()
        model_inputs = [i for i in schema.inputs if i.id == "model"]
        assert len(model_inputs) == 1
        assert set(model_inputs[0].options) == set(OpenAIClient.MODELS.keys())

    def test_chat_model_options(self):
        from openai.openai_api.client import OpenAIClient
        cls = _import_node("nodes", "OpenAIChat")
        schema = cls.define_schema()
        model_inputs = [i for i in schema.inputs if i.id == "model"]
        assert len(model_inputs) == 1
        assert set(model_inputs[0].options) == set(OpenAIClient.MODELS.keys())

    def test_vision_model_options(self):
        cls = _import_node("nodes", "OpenAIVision")
        schema = cls.define_schema()
        model_inputs = [i for i in schema.inputs if i.id == "model"]
        assert len(model_inputs) == 1
        expected = ["gpt-5.2", "gpt-5.2-pro", "gpt-5.1", "gpt-5", "gpt-5-mini",
                     "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4o", "gpt-4o-mini"]
        assert set(model_inputs[0].options) == set(expected)

    def test_image_gen_model_options(self):
        from openai.openai_api.client import OpenAIClient
        cls = _import_node("image_nodes", "OpenAIImageGeneration")
        schema = cls.define_schema()
        model_inputs = [i for i in schema.inputs if i.id == "model"]
        assert len(model_inputs) == 1
        assert set(model_inputs[0].options) == set(OpenAIClient.IMAGE_MODELS.keys())

    def test_image_edit_model_options(self):
        cls = _import_node("image_nodes", "OpenAIImageEdit")
        schema = cls.define_schema()
        model_inputs = [i for i in schema.inputs if i.id == "model"]
        assert len(model_inputs) == 1
        expected = ["gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini"]
        assert set(model_inputs[0].options) == set(expected)


class TestOpenAINoDuplicateIds:
    """No duplicate node_ids across all OpenAI nodes."""

    def test_no_duplicate_node_ids(self):
        ids = []
        for module, class_name, *_ in OPENAI_NODES:
            cls = _import_node(module, class_name)
            schema = cls.define_schema()
            ids.append(schema.node_id)
        assert len(ids) == len(set(ids)), f"Duplicate node_ids: {ids}"


class TestOpenAIProviderExport:
    """openai/__init__.py exports NODES list for ERPKExtension."""

    def test_nodes_list_exported(self):
        import importlib
        mod = importlib.import_module("openai")
        assert hasattr(mod, "NODES"), "openai package must export NODES"
        assert isinstance(mod.NODES, list)

    def test_nodes_list_has_all_classes(self):
        import importlib
        mod = importlib.import_module("openai")
        assert len(mod.NODES) == 7, f"Expected 7 OpenAI nodes, got {len(mod.NODES)}"

    def test_nodes_list_all_comfy_nodes(self):
        import importlib
        mod = importlib.import_module("openai")
        for cls in mod.NODES:
            assert issubclass(cls, IO.ComfyNode), \
                f"{cls.__name__} in NODES must inherit IO.ComfyNode"
