# ABOUTME: Tests that all API-calling nodes have seed + fingerprint_inputs for cache-busting.
# ABOUTME: Ensures re-queuing a prompt always re-executes generation nodes.

"""
Validates that every node with not_idempotent=True has a seed input with
control_after_generate set. The seed widget replaces the old fingerprint_inputs
NaN hack — when set to "randomize" (default), the seed changes each queue,
busting the cache. When "fixed", the user gets cached/reproducible results.
"""

import importlib
import pytest

IO = pytest.importorskip("comfy_api.latest").IO


# (module_path, class_name) for every node that makes API calls
API_NODES = [
    # Gemini
    ("gemini.nodes", "GeminiTextGeneration"),
    ("gemini.nodes", "GeminiChat"),
    ("gemini.nodes", "GeminiVision"),
    ("gemini.nodes", "GeminiImageGeneration"),
    ("gemini.nodes", "GeminiImageEdit"),
    ("gemini.veo_nodes", "VeoTextToVideo"),
    ("gemini.veo_nodes", "VeoImageToVideo"),
    # OpenAI
    ("openai.nodes", "OpenAITextGeneration"),
    ("openai.nodes", "OpenAIChat"),
    ("openai.nodes", "OpenAIVision"),
    ("openai.image_nodes", "OpenAIImageGeneration"),
    ("openai.image_nodes", "OpenAIImageEdit"),
    # Claude
    ("claude.text_generation", "ClaudeTextGeneration"),
    ("claude.conversation", "ClaudeConversation"),
    ("claude.vision_analysis", "ClaudeVisionAnalysis"),
    ("claude.prompt_enhancer", "ClaudePromptEnhancer"),
    ("claude.structured_output", "ClaudeStructuredOutput"),
    # WaveSpeed
    ("wavespeed.dreamina_edit", "DreaminaEditNode"),
    ("wavespeed.dreamina_text_to_image", "DreaminaTextToImageNode"),
    ("wavespeed.jibmix_qwen_image", "JibMixQwenImageNode"),
    ("wavespeed.qwen_image_edit", "QwenImageEditNode"),
    ("wavespeed.qwen_image_edit_lora", "QwenImageEditLoraNode"),
    ("wavespeed.qwen_image_edit_plus", "QwenImageEditPlusNode"),
    ("wavespeed.qwen_image_edit_plus_lora", "QwenImageEditPlusLoraNode"),
    ("wavespeed.qwen_image_layered", "QwenImageLayeredNode"),
    ("wavespeed.qwen_image_lora", "QwenImageLoraNode"),
    ("wavespeed.qwen_image_max", "QwenImageMaxNode"),
    ("wavespeed.qwen_image_max_edit", "QwenImageMaxEditNode"),
    ("wavespeed.qwen_image_multiple_angles", "QwenImageMultipleAnglesNode"),
    ("wavespeed.qwen_image_text_to_image", "QwenImageTextToImageNode"),
    ("wavespeed.seedream_v4", "SeedreamV4Node"),
    ("wavespeed.seedream_v4_edit", "SeedreamV4EditNode"),
    ("wavespeed.seedream_v4_sequential", "SeedreamV4SequentialNode"),
    ("wavespeed.seedream_v4_edit_sequential", "SeedreamV4EditSequentialNode"),
    ("wavespeed.seedream_v4_5", "SeedreamV4_5Node"),
    ("wavespeed.seedream_v4_5_edit", "SeedreamV4_5EditNode"),
    ("wavespeed.seedream_v4_5_sequential", "SeedreamV4_5SequentialNode"),
    ("wavespeed.seedream_v4_5_edit_sequential", "SeedreamV4_5EditSequentialNode"),
    ("wavespeed.seedream_v5_lite", "SeedreamV5LiteNode"),
    ("wavespeed.seedream_v5_lite_edit", "SeedreamV5LiteEditNode"),
    ("wavespeed.seedream_v5_lite_sequential", "SeedreamV5LiteSequentialNode"),
    ("wavespeed.seedream_v5_lite_edit_sequential", "SeedreamV5LiteEditSequentialNode"),
]


def _load_class(module_path, class_name):
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


@pytest.mark.parametrize("module_path,class_name", API_NODES,
                         ids=[f"{m}.{c}" for m, c in API_NODES])
class TestCacheBusting:
    """Every API-calling node must bypass ComfyUI's execution cache via seed."""

    def test_not_idempotent_is_true(self, module_path, class_name):
        cls = _load_class(module_path, class_name)
        schema = cls.define_schema()
        assert schema.not_idempotent is True, (
            f"{class_name} makes API calls but not_idempotent is not True"
        )

    def test_has_seed_input(self, module_path, class_name):
        cls = _load_class(module_path, class_name)
        schema = cls.define_schema()
        seed_inputs = [i for i in schema.inputs if i.id == "seed"]
        assert len(seed_inputs) == 1, (
            f"{class_name} must have a 'seed' input for cache-busting"
        )

    def test_seed_has_control_after_generate(self, module_path, class_name):
        cls = _load_class(module_path, class_name)
        schema = cls.define_schema()
        seed_input = next(i for i in schema.inputs if i.id == "seed")
        assert seed_input.control_after_generate is not None, (
            f"{class_name} seed input must have control_after_generate set"
        )

    def test_fingerprint_returns_nan_for_random_seed(self, module_path, class_name):
        cls = _load_class(module_path, class_name)
        assert hasattr(cls, "fingerprint_inputs"), (
            f"{class_name} must define fingerprint_inputs for cache control"
        )
        import math
        result = cls.fingerprint_inputs(seed=-1)
        assert isinstance(result, float) and math.isnan(result), (
            f"{class_name}.fingerprint_inputs(seed=-1) should return NaN, got {result!r}"
        )

    def test_fingerprint_returns_seed_for_fixed_seed(self, module_path, class_name):
        cls = _load_class(module_path, class_name)
        result = cls.fingerprint_inputs(seed=42)
        assert result == 42, (
            f"{class_name}.fingerprint_inputs(seed=42) should return 42, got {result!r}"
        )
