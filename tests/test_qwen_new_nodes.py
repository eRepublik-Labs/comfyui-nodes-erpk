# ABOUTME: Tests for new Qwen Image nodes (Multiple Angles, LoRA, Layered).
# ABOUTME: Validates request classes, node schemas, and payload structures.

"""
Tests for new Qwen Image endpoints.

Validates:
- Multiple Angles: request API path, angle params, optional prompt, images required
- LoRA: request API path, loras array, max 1024x1024, payload structure
- Layered: request API path, num_layers, no seed/size/output_format, RGBA output
- Node schemas: correct inputs, outputs, defaults
"""

import pytest

IO = pytest.importorskip("comfy_api.latest").IO


def _import_request(module_name, class_name):
    """Import a request class from the wavespeed_api.requests package."""
    import importlib
    mod = importlib.import_module(f"wavespeed.wavespeed_api.requests.{module_name}")
    return getattr(mod, class_name)


def _import_node(module_name, class_name):
    """Import a node class from the wavespeed package."""
    import importlib
    mod = importlib.import_module(f"wavespeed.{module_name}")
    return getattr(mod, class_name)


# ── Multiple Angles Request ──────────────────────────────────────────────────


class TestQwenMultipleAnglesRequest:
    """QwenImageMultipleAngles request for angle-based image editing."""

    def test_api_path(self):
        cls = _import_request("qwen_image_multiple_angles", "QwenImageMultipleAngles")
        request = cls(images=["http://example.com/img.jpg"])
        assert request.get_api_path() == "/api/v3/wavespeed-ai/qwen-image/edit-2509-multiple-angles"

    def test_required_fields(self):
        cls = _import_request("qwen_image_multiple_angles", "QwenImageMultipleAngles")
        request = cls(images=["http://example.com/img.jpg"])
        assert "images" in request.field_required()

    def test_prompt_not_required(self):
        cls = _import_request("qwen_image_multiple_angles", "QwenImageMultipleAngles")
        request = cls(images=["http://example.com/img.jpg"])
        assert "prompt" not in request.field_required()

    def test_payload_includes_angles(self):
        cls = _import_request("qwen_image_multiple_angles", "QwenImageMultipleAngles")
        request = cls(
            images=["http://example.com/img.jpg"],
            horizontal_angle=45,
            vertical_angle=30,
            distance=1.5,
        )
        payload = request.build_payload()
        assert payload["horizontal_angle"] == 45
        assert payload["vertical_angle"] == 30
        assert payload["distance"] == 1.5

    def test_payload_omits_none_values(self):
        cls = _import_request("qwen_image_multiple_angles", "QwenImageMultipleAngles")
        request = cls(images=["http://example.com/img.jpg"])
        payload = request.build_payload()
        assert "prompt" not in payload
        assert "horizontal_angle" not in payload

    def test_images_max_three(self):
        cls = _import_request("qwen_image_multiple_angles", "QwenImageMultipleAngles")
        with pytest.raises(Exception):
            cls(images=["a", "b", "c", "d"])


# ── Multiple Angles Node ─────────────────────────────────────────────────────


class TestQwenMultipleAnglesNode:
    """QwenImageMultipleAnglesNode schema and configuration."""

    def test_schema_has_images_input(self):
        cls = _import_node("qwen_image_multiple_angles", "QwenImageMultipleAnglesNode")
        schema = cls.define_schema()
        images_inputs = [i for i in schema.inputs if i.id == "images"]
        assert len(images_inputs) == 1

    def test_schema_has_angle_inputs(self):
        cls = _import_node("qwen_image_multiple_angles", "QwenImageMultipleAnglesNode")
        schema = cls.define_schema()
        input_ids = [i.id for i in schema.inputs]
        assert "horizontal_angle" in input_ids
        assert "vertical_angle" in input_ids
        assert "distance" in input_ids

    def test_prompt_is_optional(self):
        cls = _import_node("qwen_image_multiple_angles", "QwenImageMultipleAnglesNode")
        schema = cls.define_schema()
        prompt_input = next(i for i in schema.inputs if i.id == "prompt")
        assert prompt_input.optional is True

    def test_node_id(self):
        cls = _import_node("qwen_image_multiple_angles", "QwenImageMultipleAnglesNode")
        schema = cls.define_schema()
        assert schema.node_id == "QwenImageMultipleAnglesNode"

    def test_category(self):
        cls = _import_node("qwen_image_multiple_angles", "QwenImageMultipleAnglesNode")
        schema = cls.define_schema()
        assert schema.category == "ERPK/WaveSpeedAI"


# ── LoRA Request ─────────────────────────────────────────────────────────────


class TestQwenLoraRequest:
    """QwenImageLora request for LoRA-enhanced text-to-image."""

    def test_api_path(self):
        cls = _import_request("qwen_image_lora", "QwenImageLora")
        request = cls(
            prompt="test",
            loras=[{"path": "http://example.com/lora.safetensors", "scale": 1.0}],
        )
        assert request.get_api_path() == "/api/v3/wavespeed-ai/qwen-image/text-to-image-lora"

    def test_required_fields(self):
        cls = _import_request("qwen_image_lora", "QwenImageLora")
        request = cls(
            prompt="test",
            loras=[{"path": "http://example.com/lora.safetensors", "scale": 1.0}],
        )
        assert "prompt" in request.field_required()
        assert "loras" in request.field_required()

    def test_payload_includes_loras(self):
        cls = _import_request("qwen_image_lora", "QwenImageLora")
        loras = [
            {"path": "http://example.com/lora1.safetensors", "scale": 1.0},
            {"path": "http://example.com/lora2.safetensors", "scale": 2.5},
        ]
        request = cls(prompt="test", loras=loras)
        payload = request.build_payload()
        assert payload["loras"] == loras
        assert payload["prompt"] == "test"

    def test_max_three_loras(self):
        cls = _import_request("qwen_image_lora", "QwenImageLora")
        loras = [
            {"path": f"http://example.com/lora{i}.safetensors", "scale": 1.0}
            for i in range(4)
        ]
        with pytest.raises(Exception):
            cls(prompt="test", loras=loras)

    def test_payload_has_standard_fields(self):
        cls = _import_request("qwen_image_lora", "QwenImageLora")
        request = cls(
            prompt="test",
            loras=[{"path": "http://example.com/lora.safetensors", "scale": 1.0}],
            size="512*512",
            seed=42,
        )
        payload = request.build_payload()
        assert payload["size"] == "512*512"
        assert payload["seed"] == 42


# ── LoRA Node ────────────────────────────────────────────────────────────────


class TestQwenLoraNode:
    """QwenImageLoraNode schema and configuration."""

    def test_schema_has_lora_inputs(self):
        cls = _import_node("qwen_image_lora", "QwenImageLoraNode")
        schema = cls.define_schema()
        input_ids = [i.id for i in schema.inputs]
        assert "lora_1_path" in input_ids
        assert "lora_1_scale" in input_ids

    def test_schema_has_optional_lora_slots(self):
        cls = _import_node("qwen_image_lora", "QwenImageLoraNode")
        schema = cls.define_schema()
        lora_2_path = next(i for i in schema.inputs if i.id == "lora_2_path")
        lora_3_path = next(i for i in schema.inputs if i.id == "lora_3_path")
        assert lora_2_path.optional is True
        assert lora_3_path.optional is True

    def test_max_dimensions_1024(self):
        cls = _import_node("qwen_image_lora", "QwenImageLoraNode")
        schema = cls.define_schema()
        width_input = next(i for i in schema.inputs if i.id == "width")
        height_input = next(i for i in schema.inputs if i.id == "height")
        assert width_input.max == 1024
        assert height_input.max == 1024

    def test_node_id(self):
        cls = _import_node("qwen_image_lora", "QwenImageLoraNode")
        schema = cls.define_schema()
        assert schema.node_id == "QwenImageLoraNode"

    def test_category(self):
        cls = _import_node("qwen_image_lora", "QwenImageLoraNode")
        schema = cls.define_schema()
        assert schema.category == "ERPK/WaveSpeedAI"


# ── Layered Request ──────────────────────────────────────────────────────────


class TestQwenLayeredRequest:
    """QwenImageLayered request for image layer decomposition."""

    def test_api_path(self):
        cls = _import_request("qwen_image_layered", "QwenImageLayered")
        request = cls(image="http://example.com/img.jpg")
        assert request.get_api_path() == "/api/v3/wavespeed-ai/qwen-image/layered"

    def test_required_fields(self):
        cls = _import_request("qwen_image_layered", "QwenImageLayered")
        request = cls(image="http://example.com/img.jpg")
        assert "image" in request.field_required()

    def test_prompt_optional(self):
        cls = _import_request("qwen_image_layered", "QwenImageLayered")
        request = cls(image="http://example.com/img.jpg")
        payload = request.build_payload()
        assert "prompt" not in payload

    def test_default_num_layers(self):
        cls = _import_request("qwen_image_layered", "QwenImageLayered")
        request = cls(image="http://example.com/img.jpg")
        payload = request.build_payload()
        assert payload["num_layers"] == 4

    def test_no_seed_or_size_fields(self):
        cls = _import_request("qwen_image_layered", "QwenImageLayered")
        request = cls(image="http://example.com/img.jpg")
        payload = request.build_payload()
        assert "seed" not in payload
        assert "size" not in payload
        assert "output_format" not in payload

    def test_payload_with_all_params(self):
        cls = _import_request("qwen_image_layered", "QwenImageLayered")
        request = cls(
            image="http://example.com/img.jpg",
            prompt="decompose into layers",
            num_layers=6,
        )
        payload = request.build_payload()
        assert payload["image"] == "http://example.com/img.jpg"
        assert payload["prompt"] == "decompose into layers"
        assert payload["num_layers"] == 6


# ── Layered Node ─────────────────────────────────────────────────────────────


class TestQwenLayeredNode:
    """QwenImageLayeredNode schema and configuration."""

    def test_schema_has_image_and_mask_outputs(self):
        cls = _import_node("qwen_image_layered", "QwenImageLayeredNode")
        schema = cls.define_schema()
        output_types = [type(o).__name__ for o in schema.outputs]
        assert "ImageOutput" in output_types or any(
            hasattr(o, "id") and o.id == "images" for o in schema.outputs
        )
        assert any(
            hasattr(o, "id") and o.id == "masks" for o in schema.outputs
        )

    def test_schema_has_num_layers_input(self):
        cls = _import_node("qwen_image_layered", "QwenImageLayeredNode")
        schema = cls.define_schema()
        num_layers = next(i for i in schema.inputs if i.id == "num_layers")
        assert num_layers.min == 2
        assert num_layers.max == 8
        assert num_layers.default == 4

    def test_prompt_is_optional(self):
        cls = _import_node("qwen_image_layered", "QwenImageLayeredNode")
        schema = cls.define_schema()
        prompt_input = next(i for i in schema.inputs if i.id == "prompt")
        assert prompt_input.optional is True

    def test_no_seed_input(self):
        cls = _import_node("qwen_image_layered", "QwenImageLayeredNode")
        schema = cls.define_schema()
        input_ids = [i.id for i in schema.inputs]
        assert "seed" not in input_ids

    def test_no_output_format_input(self):
        cls = _import_node("qwen_image_layered", "QwenImageLayeredNode")
        schema = cls.define_schema()
        input_ids = [i.id for i in schema.inputs]
        assert "output_format" not in input_ids

    def test_node_id(self):
        cls = _import_node("qwen_image_layered", "QwenImageLayeredNode")
        schema = cls.define_schema()
        assert schema.node_id == "QwenImageLayeredNode"

    def test_category(self):
        cls = _import_node("qwen_image_layered", "QwenImageLayeredNode")
        schema = cls.define_schema()
        assert schema.category == "ERPK/WaveSpeedAI"
