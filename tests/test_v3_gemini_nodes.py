# ABOUTME: V3 structural and behavioral tests for all Gemini provider nodes.
# ABOUTME: Validates V3 compliance, custom types, model COMBO lists, and provider export.

"""
V3 tests for Gemini provider nodes (10 nodes total).

Validates:
- All classes inherit from IO.ComfyNode
- define_schema returns correct Schema with expected fields
- execute is a @classmethod
- Custom types (GEMINI_API_CLIENT, GEMINI_CHAT_SESSION) in schemas
- not_idempotent and is_output_node flags match V1 behavior
- Model COMBO options sourced from GeminiClient constants
"""

import inspect
import pytest

IO = pytest.importorskip("comfy_api.latest").IO


def _import_node(module_name, class_name):
    """Import a node class from the gemini package."""
    import importlib
    mod = importlib.import_module(f"gemini.{module_name}")
    return getattr(mod, class_name)


# --- Parametrized structural data for all 10 nodes ---
# (module, class_name, node_id, display_name, category, not_idempotent, is_output_node)
GEMINI_NODES = [
    ("nodes", "GeminiAPIConfig", "GeminiAPIConfig",
     "Gemini API Config", "ERPK/Gemini", False, False),
    ("nodes", "GeminiTextGeneration", "GeminiTextGeneration",
     "Gemini Text Generation", "ERPK/Gemini", True, False),
    ("nodes", "GeminiChat", "GeminiChat",
     "Gemini Chat", "ERPK/Gemini", True, False),
    ("nodes", "GeminiVision", "GeminiVision",
     "Gemini Vision", "ERPK/Gemini", True, False),
    ("nodes", "GeminiSystemInstruction", "GeminiSystemInstruction",
     "Gemini System Instruction", "ERPK/Gemini", False, False),
    ("nodes", "GeminiSafetySettings", "GeminiSafetySettings",
     "Gemini Safety Settings", "ERPK/Gemini", False, False),
    ("nodes", "GeminiImageGeneration", "GeminiImageGeneration",
     "Gemini Image Generation", "ERPK/Gemini", True, False),
    ("nodes", "GeminiImageEdit", "GeminiImageEdit",
     "Gemini Image Edit", "ERPK/Gemini", True, False),
    ("veo_nodes", "VeoTextToVideo", "VeoTextToVideo",
     "Veo Text to Video", "ERPK/Gemini/Veo", True, False),
    ("veo_nodes", "VeoImageToVideo", "VeoImageToVideo",
     "Veo Image to Video", "ERPK/Gemini/Veo", True, False),
]


@pytest.fixture(params=GEMINI_NODES, ids=[n[2] for n in GEMINI_NODES])
def node_spec(request):
    """Yield (cls, node_id, display_name, category, not_idempotent, is_output_node)."""
    module, class_name, node_id, display_name, category, not_idempotent, is_output_node = request.param
    cls = _import_node(module, class_name)
    return cls, node_id, display_name, category, not_idempotent, is_output_node


class TestGeminiV3Compliance:
    """All Gemini nodes comply with V3 API requirements."""

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


class TestGeminiCustomTypes:
    """Custom types appear correctly in schemas."""

    def test_api_config_outputs_client(self):
        cls = _import_node("nodes", "GeminiAPIConfig")
        schema = cls.define_schema()
        output_types = [o.io_type for o in schema.outputs]
        assert "GEMINI_API_CLIENT" in output_types

    def test_system_instruction_accepts_client(self):
        cls = _import_node("nodes", "GeminiSystemInstruction")
        schema = cls.define_schema()
        input_types = [i.io_type for i in schema.inputs]
        assert "GEMINI_API_CLIENT" in input_types

    def test_system_instruction_outputs_client(self):
        cls = _import_node("nodes", "GeminiSystemInstruction")
        schema = cls.define_schema()
        output_types = [o.io_type for o in schema.outputs]
        assert "GEMINI_API_CLIENT" in output_types

    def test_safety_settings_accepts_client(self):
        cls = _import_node("nodes", "GeminiSafetySettings")
        schema = cls.define_schema()
        input_types = [i.io_type for i in schema.inputs]
        assert "GEMINI_API_CLIENT" in input_types

    def test_safety_settings_outputs_client(self):
        cls = _import_node("nodes", "GeminiSafetySettings")
        schema = cls.define_schema()
        output_types = [o.io_type for o in schema.outputs]
        assert "GEMINI_API_CLIENT" in output_types

    def test_text_gen_accepts_optional_client(self):
        cls = _import_node("nodes", "GeminiTextGeneration")
        schema = cls.define_schema()
        client_inputs = [i for i in schema.inputs if i.id == "client"]
        assert len(client_inputs) == 1
        assert client_inputs[0].optional is True
        assert client_inputs[0].io_type == "GEMINI_API_CLIENT"

    def test_chat_accepts_optional_client(self):
        cls = _import_node("nodes", "GeminiChat")
        schema = cls.define_schema()
        client_inputs = [i for i in schema.inputs if i.id == "client"]
        assert len(client_inputs) == 1
        assert client_inputs[0].optional is True

    def test_chat_accepts_chat_session(self):
        cls = _import_node("nodes", "GeminiChat")
        schema = cls.define_schema()
        input_types = [i.io_type for i in schema.inputs]
        assert "GEMINI_CHAT_SESSION" in input_types

    def test_chat_outputs_chat_session(self):
        cls = _import_node("nodes", "GeminiChat")
        schema = cls.define_schema()
        output_types = [o.io_type for o in schema.outputs]
        assert "GEMINI_CHAT_SESSION" in output_types

    def test_vision_accepts_image(self):
        cls = _import_node("nodes", "GeminiVision")
        schema = cls.define_schema()
        input_types = [i.io_type for i in schema.inputs]
        assert "IMAGE" in input_types

    def test_image_gen_outputs_image(self):
        cls = _import_node("nodes", "GeminiImageGeneration")
        schema = cls.define_schema()
        output_types = [o.io_type for o in schema.outputs]
        assert "IMAGE" in output_types

    def test_image_edit_accepts_and_outputs_image(self):
        cls = _import_node("nodes", "GeminiImageEdit")
        schema = cls.define_schema()
        input_types = [i.io_type for i in schema.inputs]
        output_types = [o.io_type for o in schema.outputs]
        assert "IMAGE" in input_types
        assert "IMAGE" in output_types

    def test_image_edit_has_additional_images_input(self):
        cls = _import_node("nodes", "GeminiImageEdit")
        schema = cls.define_schema()
        addl = [i for i in schema.inputs if i.id == "additional_images"]
        assert len(addl) == 1
        assert addl[0].optional is True
        assert addl[0].io_type == "IMAGE"

    def test_veo_text_to_video_accepts_required_client(self):
        cls = _import_node("veo_nodes", "VeoTextToVideo")
        schema = cls.define_schema()
        client_inputs = [i for i in schema.inputs if i.id == "client"]
        assert len(client_inputs) == 1
        assert client_inputs[0].optional is False

    def test_veo_image_to_video_accepts_image(self):
        cls = _import_node("veo_nodes", "VeoImageToVideo")
        schema = cls.define_schema()
        input_types = [i.io_type for i in schema.inputs]
        assert "IMAGE" in input_types
        assert "GEMINI_API_CLIENT" in input_types


class TestGeminiModelOptions:
    """Model COMBO options are correctly sourced from GeminiClient constants."""

    def test_text_gen_model_options(self):
        from gemini.gemini_api.client import GeminiClient
        cls = _import_node("nodes", "GeminiTextGeneration")
        schema = cls.define_schema()
        model_inputs = [i for i in schema.inputs if i.id == "model"]
        assert len(model_inputs) == 1
        assert set(model_inputs[0].options) == set(GeminiClient.MODELS.keys())

    def test_chat_model_options(self):
        from gemini.gemini_api.client import GeminiClient
        cls = _import_node("nodes", "GeminiChat")
        schema = cls.define_schema()
        model_inputs = [i for i in schema.inputs if i.id == "model"]
        assert len(model_inputs) == 1
        assert set(model_inputs[0].options) == set(GeminiClient.MODELS.keys())

    def test_vision_model_options(self):
        from gemini.gemini_api.client import GeminiClient
        cls = _import_node("nodes", "GeminiVision")
        schema = cls.define_schema()
        model_inputs = [i for i in schema.inputs if i.id == "model"]
        assert len(model_inputs) == 1
        assert set(model_inputs[0].options) == set(GeminiClient.MODELS.keys())

    def test_image_gen_model_options(self):
        from gemini.gemini_api.client import GeminiClient
        cls = _import_node("nodes", "GeminiImageGeneration")
        schema = cls.define_schema()
        model_inputs = [i for i in schema.inputs if i.id == "model"]
        assert len(model_inputs) == 1
        assert set(model_inputs[0].options) == set(GeminiClient.IMAGE_MODELS)

    def test_image_edit_model_options(self):
        from gemini.gemini_api.client import GeminiClient
        cls = _import_node("nodes", "GeminiImageEdit")
        schema = cls.define_schema()
        model_inputs = [i for i in schema.inputs if i.id == "model"]
        assert len(model_inputs) == 1
        assert set(model_inputs[0].options) == set(GeminiClient.IMAGE_MODELS)


class TestGeminiNoDuplicateIds:
    """No duplicate node_ids across all Gemini nodes."""

    def test_no_duplicate_node_ids(self):
        ids = []
        for module, class_name, *_ in GEMINI_NODES:
            cls = _import_node(module, class_name)
            schema = cls.define_schema()
            ids.append(schema.node_id)
        assert len(ids) == len(set(ids)), f"Duplicate node_ids: {ids}"


class TestGeminiProviderExport:
    """gemini/__init__.py exports NODES list for ERPKExtension."""

    def test_nodes_list_exported(self):
        import importlib
        mod = importlib.import_module("gemini")
        assert hasattr(mod, "NODES"), "gemini package must export NODES"
        assert isinstance(mod.NODES, list)

    def test_nodes_list_has_all_classes(self):
        import importlib
        mod = importlib.import_module("gemini")
        assert len(mod.NODES) == 10, f"Expected 10 Gemini nodes, got {len(mod.NODES)}"

    def test_nodes_list_all_comfy_nodes(self):
        import importlib
        mod = importlib.import_module("gemini")
        for cls in mod.NODES:
            assert issubclass(cls, IO.ComfyNode), \
                f"{cls.__name__} in NODES must inherit IO.ComfyNode"
