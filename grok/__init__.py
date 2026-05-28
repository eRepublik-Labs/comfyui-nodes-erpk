# ABOUTME: Grok (xAI) provider V3 node registration for ERPKExtension aggregation.
# ABOUTME: Exports the NODES list consumed by the top-level __init__.py provider loop.

from .nodes import GrokAPIClient, GrokTextGeneration, GrokChat, GrokImageGeneration, GrokImageEdit
from .video_nodes import GrokTextToVideo, GrokRefToVideo, GrokVideoEdit, GrokVideoExtend

NODES = [
    GrokAPIClient,
    GrokTextGeneration,
    GrokChat,
    GrokImageGeneration,
    GrokImageEdit,
    GrokTextToVideo,
    GrokRefToVideo,
    GrokVideoEdit,
    GrokVideoExtend,
]

__all__ = ["NODES"]
