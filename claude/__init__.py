# ABOUTME: Claude provider nodes for ComfyUI V3 API.
# ABOUTME: Exports all Claude node classes for registration via comfy_entrypoint.

from .nodes import ClaudeAPIClient, ClaudeUsageStats
from .text_generation import ClaudeTextGeneration
from .prompt_enhancer import ClaudePromptEnhancer
from .vision_analysis import ClaudeVisionAnalysis
from .conversation import ClaudeConversation, ClaudeConversationInfo
from .token_counter import ClaudeTokenCounter
from .tool_definition import ClaudeToolDefinition
from .structured_output import ClaudeStructuredOutput

NODES = [
    ClaudeAPIClient,
    ClaudeUsageStats,
    ClaudeTextGeneration,
    ClaudePromptEnhancer,
    ClaudeVisionAnalysis,
    ClaudeConversation,
    ClaudeConversationInfo,
    ClaudeTokenCounter,
    ClaudeToolDefinition,
    ClaudeStructuredOutput,
]

__all__ = ["NODES"]
