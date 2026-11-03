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
from .omni_nodes import GeminiOmniReferenceToVideo, GeminiOmniVideoGeneration

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
    GeminiOmniVideoGeneration,
    GeminiOmniReferenceToVideo,
]

__all__ = ["NODES"]
