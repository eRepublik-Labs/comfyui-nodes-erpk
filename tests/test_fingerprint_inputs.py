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
    ("erpk.gemini.nodes", "GeminiTextGeneration"),
    ("erpk.gemini.nodes", "GeminiChat"),
    ("erpk.gemini.nodes", "GeminiVision"),
    ("erpk.gemini.nodes", "GeminiDetect"),
    ("erpk.gemini.nodes", "GeminiImageGeneration"),
    ("erpk.gemini.nodes", "GeminiImageEdit"),
    ("erpk.gemini.omni_nodes", "GeminiOmniVideoGeneration"),
    ("erpk.gemini.omni_nodes", "GeminiOmniReferenceToVideo"),
    # OpenAI
    ("erpk.openai.nodes", "OpenAITextGeneration"),
    ("erpk.openai.nodes", "OpenAIChat"),
    ("erpk.openai.nodes", "OpenAIVision"),
    ("erpk.openai.image_nodes", "OpenAIImageGeneration"),
    ("erpk.openai.image_nodes", "OpenAIImageEdit"),
    # Claude
    ("claude.text_generation", "ClaudeTextGeneration"),
    ("claude.conversation", "ClaudeConversation"),
    ("claude.vision_analysis", "ClaudeVisionAnalysis"),
    ("claude.prompt_enhancer", "ClaudePromptEnhancer"),
    ("claude.structured_output", "ClaudeStructuredOutput"),
    # WaveSpeed
    ("erpk.wavespeed.dreamina_edit", "DreaminaEditNode"),
    ("erpk.wavespeed.dreamina_text_to_image", "DreaminaTextToImageNode"),
    ("erpk.wavespeed.jibmix_qwen_image", "JibMixQwenImageNode"),
    ("erpk.wavespeed.qwen_image_edit", "QwenImageEditNode"),
    ("erpk.wavespeed.qwen_image_edit_lora", "QwenImageEditLoraNode"),
    ("erpk.wavespeed.qwen_image_edit_plus", "QwenImageEditPlusNode"),
    ("erpk.wavespeed.qwen_image_edit_plus_lora", "QwenImageEditPlusLoraNode"),
    ("erpk.wavespeed.qwen_image_layered", "QwenImageLayeredNode"),
    ("erpk.wavespeed.qwen_image_lora", "QwenImageLoraNode"),
    ("erpk.wavespeed.qwen_image_max", "QwenImageMaxNode"),
    ("erpk.wavespeed.qwen_image_max_edit", "QwenImageMaxEditNode"),
    ("erpk.wavespeed.qwen_image_multiple_angles", "QwenImageMultipleAnglesNode"),
    ("erpk.wavespeed.qwen_image_multiple_angles_96", "QwenImageMultipleAngles96Node"),
    ("erpk.wavespeed.qwen_image_3_0_text_to_image", "QwenImage30TextToImageNode"),
    ("erpk.wavespeed.qwen_image_3_0_edit", "QwenImage30EditNode"),
    ("erpk.wavespeed.qwen_image_text_to_image", "QwenImageTextToImageNode"),
    ("erpk.wavespeed.minimax_h3_text_to_video", "MinimaxH3TextToVideoNode"),
    ("erpk.wavespeed.minimax_h3_image_to_video", "MinimaxH3ImageToVideoNode"),
    ("erpk.wavespeed.minimax_h3_reference_to_video", "MinimaxH3ReferenceToVideoNode"),
    ("erpk.wavespeed.minimax_h3_text_to_image", "MinimaxH3TextToImageNode"),
    ("erpk.wavespeed.minimax_h3_image_edit", "MinimaxH3ImageEditNode"),
    ("erpk.wavespeed.minimax_h3_video_edit", "MinimaxH3VideoEditNode"),
    ("erpk.wavespeed.minimax_h3_video_extend", "MinimaxH3VideoExtendNode"),
    ("erpk.wavespeed.seedance_2_5_text_to_video", "Seedance25TextToVideoNode"),
    ("erpk.wavespeed.seedance_2_5_image_to_video", "Seedance25ImageToVideoNode"),
    ("erpk.wavespeed.seedance_2_5_video_edit", "Seedance25VideoEditNode"),
    ("erpk.wavespeed.seedance_2_5_video_extend", "Seedance25VideoExtendNode"),
    ("erpk.wavespeed.seedream_v4", "SeedreamV4Node"),
    ("erpk.wavespeed.seedream_v4_edit", "SeedreamV4EditNode"),
    ("erpk.wavespeed.seedream_v4_sequential", "SeedreamV4SequentialNode"),
    ("erpk.wavespeed.seedream_v4_edit_sequential", "SeedreamV4EditSequentialNode"),
    ("erpk.wavespeed.seedream_v4_5", "SeedreamV4_5Node"),
    ("erpk.wavespeed.seedream_v4_5_edit", "SeedreamV4_5EditNode"),
    ("erpk.wavespeed.seedream_v4_5_sequential", "SeedreamV4_5SequentialNode"),
    ("erpk.wavespeed.seedream_v4_5_edit_sequential", "SeedreamV4_5EditSequentialNode"),
    ("erpk.wavespeed.seedream_v5_lite", "SeedreamV5LiteNode"),
    ("erpk.wavespeed.seedream_v5_lite_edit", "SeedreamV5LiteEditNode"),
    ("erpk.wavespeed.seedream_v5_pro", "SeedreamV5ProNode"),
    ("erpk.wavespeed.seedream_v5_pro_edit", "SeedreamV5ProEditNode"),
    ("erpk.wavespeed.seedream_v5_pro_layers", "SeedreamV5ProLayersNode"),
    ("erpk.wavespeed.seedream_v5_lite_sequential", "SeedreamV5LiteSequentialNode"),
    ("erpk.wavespeed.seedream_v5_lite_edit_sequential", "SeedreamV5LiteEditSequentialNode"),
    # WaveSpeed video (Kling / LTX 2 Pro) — seed is cache-control only; these
    # endpoints have no API seed parameter, so a fixed seed reuses the cached
    # result rather than reproducing a deterministic generation.
    ("erpk.wavespeed.kling_elements", "KlingElementsNode"),
    ("erpk.wavespeed.kling_v2_5_turbo_text_to_video", "KlingV2_5TurboTextToVideoNode"),
    ("erpk.wavespeed.kling_v2_5_turbo_image_to_video", "KlingV2_5TurboImageToVideoNode"),
    ("erpk.wavespeed.kling_v2_6_text_to_video", "KlingV2_6TextToVideoNode"),
    ("erpk.wavespeed.kling_v2_6_image_to_video", "KlingV2_6ImageToVideoNode"),
    ("erpk.wavespeed.ltx_2_pro_text_to_video", "Ltx2ProTextToVideoNode"),
    ("erpk.wavespeed.ltx_2_pro_image_to_video", "Ltx2ProImageToVideoNode"),
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


# Config / passthrough nodes: no API call, no seed input. They must NOT define
# fingerprint_inputs — a seedless node copies the NaN branch unconditionally
# (kwargs.get("seed", -1) is always -1), marking itself dirty every queue. As a
# root, that cascades cache invalidation into every downstream node, re-billing
# the whole graph. These rely on ComfyUI's default input-based caching instead.
CONFIG_NODES = [
    ("erpk.gemini.nodes", "GeminiAPIConfig"),
    ("erpk.gemini.nodes", "GeminiSystemInstruction"),
    ("erpk.gemini.nodes", "GeminiSafetySettings"),
    ("utils.regional_prompt", "RegionalPromptBuilder"),
    ("utils.image_grid_loader", "ImageGridLoader"),
    ("erpk.openai.nodes", "OpenAIAPIConfig"),
    ("erpk.openai.nodes", "OpenAISystemInstruction"),
    ("erpk.wavespeed.minimax_h3_lora_stack", "MinimaxH3LoraStackNode"),
]


@pytest.mark.parametrize("module_path,class_name", CONFIG_NODES,
                         ids=[f"{m}.{c}" for m, c in CONFIG_NODES])
class TestConfigNodesAreCacheable:
    """Non-API config/passthrough nodes must not force re-execution every queue."""

    def test_no_seed_input(self, module_path, class_name):
        cls = _load_class(module_path, class_name)
        schema = cls.define_schema()
        assert not [i for i in schema.inputs if i.id == "seed"], (
            f"{class_name} is treated as a config node but declares a seed input"
        )

    def test_does_not_declare_fingerprint_inputs(self, module_path, class_name):
        cls = _load_class(module_path, class_name)
        assert "fingerprint_inputs" not in cls.__dict__, (
            f"{class_name} has no seed input, so its fingerprint_inputs always "
            f"returns NaN — marking it dirty every queue and cascading cache "
            f"invalidation downstream. Remove the method; rely on default caching."
        )
