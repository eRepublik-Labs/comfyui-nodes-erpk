# ABOUTME: OpenAI provider V3 node registration
# ABOUTME: Exports all OpenAI nodes for ERPKExtension aggregation

from .nodes import (
    OpenAIAPIConfig, OpenAITextGeneration, OpenAIChat, OpenAIVision,
    OpenAISystemInstruction,
)
from .image_nodes import OpenAIImageGeneration, OpenAIImageEdit

NODES = [
    OpenAIAPIConfig, OpenAITextGeneration, OpenAIChat, OpenAIVision,
    OpenAISystemInstruction, OpenAIImageGeneration, OpenAIImageEdit,
]

__all__ = ["NODES"]
