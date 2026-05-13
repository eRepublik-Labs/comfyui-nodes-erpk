# ABOUTME: V3 structural and behavioral tests for all WaveSpeed provider nodes.
# ABOUTME: Validates V3 compliance, custom types, size presets, and provider export (31 nodes).

"""
V3 tests for WaveSpeed provider nodes (31 nodes total).

Validates:
- All classes inherit from IO.ComfyNode
- define_schema returns correct Schema with expected fields
- execute is a @classmethod
- Custom types (WAVESPEED_AI_API_CLIENT) in schemas
- not_idempotent and is_output_node flags match V1 behavior
- Size preset COMBO options match expected constants
"""

import inspect
import pytest

IO = pytest.importorskip("comfy_api.latest").IO


def _import_node(module_name, class_name):
    """Import a node class from the wavespeed package."""
    import importlib
    mod = importlib.import_module(f"wavespeed.{module_name}")
    return getattr(mod, class_name)


# --- Parametrized structural data for all 18 nodes ---
# (module, class_name, node_id, display_name, category, not_idempotent, is_output_node)
WAVESPEED_NODES = [
    # Core nodes (nodes.py)
    ("nodes", "WaveSpeedAIAPIClient", "WaveSpeedAIAPIClient",
     "WaveSpeed Client", "ERPK/WaveSpeedAI", False, False),
    ("nodes", "PreviewVideo", "PreviewVideo",
     "WaveSpeed Preview Video", "ERPK/WaveSpeedAI", False, True),
    ("nodes", "SaveAudio", "SaveAudio",
     "WaveSpeed Save Audio", "ERPK/WaveSpeedAI", False, True),
    ("nodes", "UploadImage", "UploadImage",
     "WaveSpeed Upload Image", "ERPK/WaveSpeedAI", False, False),
    # Seedream V4 nodes
    ("seedream_v4", "SeedreamV4Node", "SeedreamV4Node",
     "Bytedance Seedream V4", "ERPK/WaveSpeedAI", True, False),
    ("seedream_v4_edit", "SeedreamV4EditNode", "SeedreamV4EditNode",
     "Bytedance Seedream V4 Edit", "ERPK/WaveSpeedAI", True, False),
    ("seedream_v4_sequential", "SeedreamV4SequentialNode", "SeedreamV4SequentialNode",
     "Bytedance Seedream V4 Sequential", "ERPK/WaveSpeedAI", True, False),
    ("seedream_v4_edit_sequential", "SeedreamV4EditSequentialNode", "SeedreamV4EditSequentialNode",
     "Bytedance Seedream V4 Edit Sequential", "ERPK/WaveSpeedAI", True, False),
    # Seedream V4.5 nodes
    ("seedream_v4_5", "SeedreamV4_5Node", "SeedreamV4_5Node",
     "Bytedance Seedream V4.5", "ERPK/WaveSpeedAI", True, False),
    ("seedream_v4_5_edit", "SeedreamV4_5EditNode", "SeedreamV4_5EditNode",
     "Bytedance Seedream V4.5 Edit", "ERPK/WaveSpeedAI", True, False),
    ("seedream_v4_5_sequential", "SeedreamV4_5SequentialNode", "SeedreamV4_5SequentialNode",
     "Bytedance Seedream V4.5 Sequential", "ERPK/WaveSpeedAI", True, False),
    ("seedream_v4_5_edit_sequential", "SeedreamV4_5EditSequentialNode", "SeedreamV4_5EditSequentialNode",
     "Bytedance Seedream V4.5 Edit Sequential", "ERPK/WaveSpeedAI", True, False),
    # Qwen Image nodes
    ("qwen_image_text_to_image", "QwenImageTextToImageNode", "QwenImageTextToImageNode",
     "Qwen Image Text-to-Image", "ERPK/WaveSpeedAI", True, False),
    ("qwen_image_edit", "QwenImageEditNode", "QwenImageEditNode",
     "Qwen Image Edit", "ERPK/WaveSpeedAI", True, False),
    ("qwen_image_edit_plus", "QwenImageEditPlusNode", "QwenImageEditPlusNode",
     "Qwen Image Edit Plus", "ERPK/WaveSpeedAI", True, False),
    ("qwen_image_multiple_angles", "QwenImageMultipleAnglesNode", "QwenImageMultipleAnglesNode",
     "Qwen Image Multiple Angles", "ERPK/WaveSpeedAI", True, False),
    ("qwen_image_lora", "QwenImageLoraNode", "QwenImageLoraNode",
     "Qwen Image LoRA", "ERPK/WaveSpeedAI", True, False),
    ("qwen_image_edit_lora", "QwenImageEditLoraNode", "QwenImageEditLoraNode",
     "Qwen Image Edit LoRA", "ERPK/WaveSpeedAI", True, False),
    ("qwen_image_edit_plus_lora", "QwenImageEditPlusLoraNode", "QwenImageEditPlusLoraNode",
     "Qwen Image Edit Plus LoRA", "ERPK/WaveSpeedAI", True, False),
    ("qwen_image_layered", "QwenImageLayeredNode", "QwenImageLayeredNode",
     "Qwen Image Layered", "ERPK/WaveSpeedAI", True, False),
    ("qwen_image_2_0_text_to_image", "QwenImage20TextToImageNode", "QwenImage20TextToImageNode",
     "Qwen Image 2.0 Text-to-Image", "ERPK/WaveSpeedAI", True, False),
    ("qwen_image_2_0_edit", "QwenImage20EditNode", "QwenImage20EditNode",
     "Qwen Image 2.0 Edit", "ERPK/WaveSpeedAI", True, False),
    # Seedream V5.0 Lite nodes
    ("seedream_v5_lite", "SeedreamV5LiteNode", "SeedreamV5LiteNode",
     "Bytedance Seedream V5.0 Lite", "ERPK/WaveSpeedAI", True, False),
    ("seedream_v5_lite_edit", "SeedreamV5LiteEditNode", "SeedreamV5LiteEditNode",
     "Bytedance Seedream V5.0 Lite Edit", "ERPK/WaveSpeedAI", True, False),
    ("seedream_v5_lite_sequential", "SeedreamV5LiteSequentialNode", "SeedreamV5LiteSequentialNode",
     "Bytedance Seedream V5.0 Lite Sequential", "ERPK/WaveSpeedAI", True, False),
    ("seedream_v5_lite_edit_sequential", "SeedreamV5LiteEditSequentialNode", "SeedreamV5LiteEditSequentialNode",
     "Bytedance Seedream V5.0 Lite Edit Sequential", "ERPK/WaveSpeedAI", True, False),
    # Qwen Image Max nodes
    ("qwen_image_max", "QwenImageMaxNode", "QwenImageMaxNode",
     "Qwen Image Max", "ERPK/WaveSpeedAI", True, False),
    ("qwen_image_max_edit", "QwenImageMaxEditNode", "QwenImageMaxEditNode",
     "Qwen Image Max Edit", "ERPK/WaveSpeedAI", True, False),
    # JibMix Qwen Image node
    ("jibmix_qwen_image", "JibMixQwenImageNode", "JibMixQwenImageNode",
     "JibMix Qwen Image", "ERPK/WaveSpeedAI", True, False),
    # Dreamina nodes
    ("dreamina_text_to_image", "DreaminaTextToImageNode", "DreaminaTextToImageNode",
     "Bytedance Dreamina Text-to-Image", "ERPK/WaveSpeedAI", True, False),
    ("dreamina_edit", "DreaminaEditNode", "DreaminaEditNode",
     "Bytedance Dreamina Edit", "ERPK/WaveSpeedAI", True, False),
    # Video nodes
    ("seedance_2_0_text_to_video", "Seedance20TextToVideoNode", "Seedance20TextToVideoNode",
     "Bytedance Seedance 2.0 Text-to-Video", "ERPK/WaveSpeedAI", True, False),
    ("seedance_2_0_image_to_video", "Seedance20ImageToVideoNode", "Seedance20ImageToVideoNode",
     "Bytedance Seedance 2.0 Image-to-Video", "ERPK/WaveSpeedAI", True, False),
    ("wan_2_7_text_to_video", "Wan27TextToVideoNode", "Wan27TextToVideoNode",
     "Alibaba WAN 2.7 Text-to-Video", "ERPK/WaveSpeedAI", True, False),
    ("wan_2_7_image_to_video", "Wan27ImageToVideoNode", "Wan27ImageToVideoNode",
     "Alibaba WAN 2.7 Image-to-Video", "ERPK/WaveSpeedAI", True, False),
    ("wan_2_7_video_extend", "Wan27VideoExtendNode", "Wan27VideoExtendNode",
     "Alibaba WAN 2.7 Video Extend", "ERPK/WaveSpeedAI", True, False),
    ("wavespeed_veo_3_1_text_to_video", "WaveSpeedVeo31TextToVideoNode", "WaveSpeedVeo31TextToVideoNode",
     "WaveSpeed Veo 3.1 Text-to-Video", "ERPK/WaveSpeedAI", True, False),
    ("wavespeed_veo_3_1_image_to_video", "WaveSpeedVeo31ImageToVideoNode", "WaveSpeedVeo31ImageToVideoNode",
     "WaveSpeed Veo 3.1 Image-to-Video", "ERPK/WaveSpeedAI", True, False),
    ("kling_v3_image_to_video", "KlingV3ImageToVideoNode", "KlingV3ImageToVideoNode",
     "Kling 3.0 Image-to-Video", "ERPK/WaveSpeedAI", True, False),
    ("kling_o3_text_to_video", "KlingO3TextToVideoNode", "KlingO3TextToVideoNode",
     "Kling O3 Text-to-Video", "ERPK/WaveSpeedAI", True, False),
    ("kling_o3_image_to_video", "KlingO3ImageToVideoNode", "KlingO3ImageToVideoNode",
     "Kling O3 Image-to-Video", "ERPK/WaveSpeedAI", True, False),
    ("ltx_2_pro_text_to_video", "Ltx2ProTextToVideoNode", "Ltx2ProTextToVideoNode",
     "Lightricks LTX 2 Pro Text-to-Video", "ERPK/WaveSpeedAI", True, False),
    ("ltx_2_pro_image_to_video", "Ltx2ProImageToVideoNode", "Ltx2ProImageToVideoNode",
     "Lightricks LTX 2 Pro Image-to-Video", "ERPK/WaveSpeedAI", True, False),
    ("ltx_2_3_text_to_video", "Ltx23TextToVideoNode", "Ltx23TextToVideoNode",
     "WaveSpeed LTX 2.3 Text-to-Video", "ERPK/WaveSpeedAI", True, False),
    ("ltx_2_3_image_to_video", "Ltx23ImageToVideoNode", "Ltx23ImageToVideoNode",
     "WaveSpeed LTX 2.3 Image-to-Video", "ERPK/WaveSpeedAI", True, False),
]


@pytest.fixture(params=WAVESPEED_NODES, ids=[n[2] for n in WAVESPEED_NODES])
def node_spec(request):
    """Yield (cls, node_id, display_name, category, not_idempotent, is_output_node)."""
    module, class_name, node_id, display_name, category, not_idempotent, is_output_node = request.param
    cls = _import_node(module, class_name)
    return cls, node_id, display_name, category, not_idempotent, is_output_node


class TestWaveSpeedV3Compliance:
    """All WaveSpeed nodes comply with V3 API requirements."""

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


class TestWaveSpeedCustomTypes:
    """Custom types appear correctly in schemas."""

    def test_client_outputs_wavespeed_client(self):
        cls = _import_node("nodes", "WaveSpeedAIAPIClient")
        schema = cls.define_schema()
        output_types = [o.io_type for o in schema.outputs]
        assert "WAVESPEED_AI_API_CLIENT" in output_types

    def test_upload_image_accepts_optional_client(self):
        cls = _import_node("nodes", "UploadImage")
        schema = cls.define_schema()
        client_inputs = [i for i in schema.inputs if i.id == "client"]
        assert len(client_inputs) == 1
        assert client_inputs[0].optional is True
        assert client_inputs[0].io_type == "WAVESPEED_AI_API_CLIENT"

    def test_upload_image_accepts_image(self):
        cls = _import_node("nodes", "UploadImage")
        schema = cls.define_schema()
        input_types = [i.io_type for i in schema.inputs]
        assert "IMAGE" in input_types

    def test_seedream_v4_accepts_optional_client(self):
        cls = _import_node("seedream_v4", "SeedreamV4Node")
        schema = cls.define_schema()
        client_inputs = [i for i in schema.inputs if i.id == "client"]
        assert len(client_inputs) == 1
        assert client_inputs[0].optional is True
        assert client_inputs[0].io_type == "WAVESPEED_AI_API_CLIENT"

    def test_seedream_v4_5_accepts_optional_client(self):
        cls = _import_node("seedream_v4_5", "SeedreamV4_5Node")
        schema = cls.define_schema()
        client_inputs = [i for i in schema.inputs if i.id == "client"]
        assert len(client_inputs) == 1
        assert client_inputs[0].optional is True
        assert client_inputs[0].io_type == "WAVESPEED_AI_API_CLIENT"

    def test_qwen_t2i_accepts_optional_client(self):
        cls = _import_node("qwen_image_text_to_image", "QwenImageTextToImageNode")
        schema = cls.define_schema()
        client_inputs = [i for i in schema.inputs if i.id == "client"]
        assert len(client_inputs) == 1
        assert client_inputs[0].optional is True
        assert client_inputs[0].io_type == "WAVESPEED_AI_API_CLIENT"

    def test_qwen_edit_accepts_optional_client(self):
        cls = _import_node("qwen_image_edit", "QwenImageEditNode")
        schema = cls.define_schema()
        client_inputs = [i for i in schema.inputs if i.id == "client"]
        assert len(client_inputs) == 1
        assert client_inputs[0].optional is True
        assert client_inputs[0].io_type == "WAVESPEED_AI_API_CLIENT"

    def test_all_model_nodes_output_image(self):
        """All generation/edit nodes output IMAGE type."""
        model_nodes = [
            ("seedream_v4", "SeedreamV4Node"),
            ("seedream_v4_edit", "SeedreamV4EditNode"),
            ("seedream_v4_sequential", "SeedreamV4SequentialNode"),
            ("seedream_v4_edit_sequential", "SeedreamV4EditSequentialNode"),
            ("seedream_v4_5", "SeedreamV4_5Node"),
            ("seedream_v4_5_edit", "SeedreamV4_5EditNode"),
            ("seedream_v4_5_sequential", "SeedreamV4_5SequentialNode"),
            ("seedream_v4_5_edit_sequential", "SeedreamV4_5EditSequentialNode"),
            ("qwen_image_text_to_image", "QwenImageTextToImageNode"),
            ("qwen_image_edit", "QwenImageEditNode"),
            ("qwen_image_edit_plus", "QwenImageEditPlusNode"),
        ]
        for module, class_name in model_nodes:
            cls = _import_node(module, class_name)
            schema = cls.define_schema()
            output_types = [o.io_type for o in schema.outputs]
            assert "IMAGE" in output_types, \
                f"{class_name} must output IMAGE type"


class TestWaveSpeedNoDuplicateIds:
    """No duplicate node_ids across all WaveSpeed nodes."""

    def test_no_duplicate_node_ids(self):
        ids = []
        for module, class_name, *_ in WAVESPEED_NODES:
            cls = _import_node(module, class_name)
            schema = cls.define_schema()
            ids.append(schema.node_id)
        assert len(ids) == len(set(ids)), f"Duplicate node_ids: {ids}"


class TestWaveSpeedProviderExport:
    """wavespeed/__init__.py exports NODES list for ERPKExtension."""

    def test_nodes_list_exported(self):
        import importlib
        mod = importlib.import_module("wavespeed")
        assert hasattr(mod, "NODES"), "wavespeed package must export NODES"
        assert isinstance(mod.NODES, list)

    def test_nodes_list_has_all_classes(self):
        import importlib
        mod = importlib.import_module("wavespeed")
        assert len(mod.NODES) == 51, f"Expected 51 WaveSpeed nodes, got {len(mod.NODES)}"

    def test_nodes_list_all_comfy_nodes(self):
        import importlib
        mod = importlib.import_module("wavespeed")
        for cls in mod.NODES:
            assert issubclass(cls, IO.ComfyNode), \
                f"{cls.__name__} in NODES must inherit IO.ComfyNode"
