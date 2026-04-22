# ABOUTME: OpenAI provider V3 node registration
# ABOUTME: Exports all OpenAI nodes for ERPKExtension aggregation

from .nodes import (
    OpenAIAPIConfig, OpenAITextGeneration, OpenAIChat, OpenAIVision,
    OpenAISystemInstruction,
)
from .image_nodes import OpenAIImageGeneration, OpenAIImageEdit, OpenAIImageResponses

NODES = [
    OpenAIAPIConfig, OpenAITextGeneration, OpenAIChat, OpenAIVision,
    OpenAISystemInstruction, OpenAIImageGeneration, OpenAIImageEdit,
    OpenAIImageResponses,
]

__all__ = ["NODES"]
