# ABOUTME: Gemini provider nodes for ComfyUI V3 API.
# ABOUTME: Exports all Gemini node classes for registration via comfy_entrypoint.

from .nodes import (
    GeminiAPIConfig,
    GeminiTextGeneration,
    GeminiChat,
    GeminiVision,
    GeminiDetect,
    GeminiSystemInstruction,
    GeminiSafetySettings,
    GeminiImageGeneration,
    GeminiImageEdit,
)
from .veo_nodes import VeoTextToVideo, VeoImageToVideo
from .omni_nodes import GeminiOmniVideoGeneration

NODES = [
    GeminiAPIConfig,
    GeminiTextGeneration,
    GeminiChat,
    GeminiVision,
    GeminiDetect,
    GeminiSystemInstruction,
    GeminiSafetySettings,
    GeminiImageGeneration,
    GeminiImageEdit,
    VeoTextToVideo,
    VeoImageToVideo,
    GeminiOmniVideoGeneration,
]

__all__ = ["NODES"]
