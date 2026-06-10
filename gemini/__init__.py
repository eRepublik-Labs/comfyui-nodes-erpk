# ABOUTME: Gemini provider nodes for ComfyUI V3 API.
# ABOUTME: Exports all Gemini node classes for registration via comfy_entrypoint.

from .nodes import (
    GeminiAPIConfig,
    GeminiTextGeneration,
    GeminiChat,
    GeminiVision,
    GeminiSystemInstruction,
    GeminiSafetySettings,
    GeminiImageGeneration,
    GeminiImageEdit,
)
from .regional_prompt import GeminiRegionalPromptBuilder
from .veo_nodes import VeoTextToVideo, VeoImageToVideo

NODES = [
    GeminiAPIConfig,
    GeminiTextGeneration,
    GeminiChat,
    GeminiVision,
    GeminiSystemInstruction,
    GeminiSafetySettings,
    GeminiImageGeneration,
    GeminiImageEdit,
    VeoTextToVideo,
    VeoImageToVideo,
    GeminiRegionalPromptBuilder,
]

__all__ = ["NODES"]
