# ABOUTME: Tests that all API-calling nodes define fingerprint_inputs for cache-busting.
# ABOUTME: Ensures re-queuing a prompt always re-executes generation nodes.

"""
Validates that every node with not_idempotent=True also defines fingerprint_inputs.

ComfyUI's not_idempotent flag only prevents cache sharing between different node
instances in the same graph. To force re-execution on every queue (even when inputs
haven't changed), nodes must override fingerprint_inputs — the V3 equivalent of
V1's IS_CHANGED.
"""

import math
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
    ("wavespeed.seedream_v4", "SeedreamV4Node"),
    ("wavespeed.seedream_v4_edit", "SeedreamV4EditNode"),
    ("wavespeed.seedream_v4_sequential", "SeedreamV4SequentialNode"),
    ("wavespeed.seedream_v4_edit_sequential", "SeedreamV4EditSequentialNode"),
    ("wavespeed.seedream_v4_5", "SeedreamV4_5Node"),
    ("wavespeed.seedream_v4_5_edit", "SeedreamV4_5EditNode"),
    ("wavespeed.seedream_v4_5_sequential", "SeedreamV4_5SequentialNode"),
    ("wavespeed.seedream_v4_5_edit_sequential", "SeedreamV4_5EditSequentialNode"),
    ("wavespeed.qwen_image_edit", "QwenImageEditNode"),
    ("wavespeed.qwen_image_edit_plus", "QwenImageEditPlusNode"),
    ("wavespeed.qwen_image_text_to_image", "QwenImageTextToImageNode"),
]


def _load_class(module_path, class_name):
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


@pytest.mark.parametrize("module_path,class_name", API_NODES,
                         ids=[f"{m}.{c}" for m, c in API_NODES])
class TestCacheBusting:
    """Every API-calling node must bypass ComfyUI's execution cache."""

    def test_not_idempotent_is_true(self, module_path, class_name):
        cls = _load_class(module_path, class_name)
        schema = cls.define_schema()
        assert schema.not_idempotent is True, (
            f"{class_name} makes API calls but not_idempotent is not True"
        )

    def test_fingerprint_inputs_defined(self, module_path, class_name):
        cls = _load_class(module_path, class_name)
        assert hasattr(cls, "fingerprint_inputs"), (
            f"{class_name} missing fingerprint_inputs — cache won't bust on re-queue"
        )
        # Must be overridden, not the base stub
        method = getattr(cls, "fingerprint_inputs")
        assert callable(method), f"{class_name}.fingerprint_inputs is not callable"

    def test_fingerprint_returns_nan(self, module_path, class_name):
        cls = _load_class(module_path, class_name)
        result = cls.fingerprint_inputs()
        assert isinstance(result, float) and math.isnan(result), (
            f"{class_name}.fingerprint_inputs() must return float('NaN'), got {result!r}"
        )
