# ABOUTME: OpenAI ComfyUI Custom Nodes package initialization
# ABOUTME: Exports all OpenAI nodes for text, vision, and image generation

import os
import sys

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Initialize combined mappings
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Import and register core nodes (Config, Text, Chat, Vision, System Instruction)
try:
    from .nodes import (
        NODE_CLASS_MAPPINGS as CORE_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as CORE_NODE_DISPLAY_NAME_MAPPINGS
    )
    NODE_CLASS_MAPPINGS.update(CORE_NODE_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(CORE_NODE_DISPLAY_NAME_MAPPINGS)
except ImportError as e:
    print(f"[OpenAI] Warning: Could not load core nodes: {e}")

# Import and register image nodes (ImageGeneration, ImageEdit)
try:
    from .image_nodes import (
        NODE_CLASS_MAPPINGS as IMAGE_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as IMAGE_NODE_DISPLAY_NAME_MAPPINGS
    )
    NODE_CLASS_MAPPINGS.update(IMAGE_NODE_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(IMAGE_NODE_DISPLAY_NAME_MAPPINGS)
except ImportError as e:
    print(f"[OpenAI] Warning: Could not load image nodes: {e}")

# Print loaded nodes for debugging
print(f"[OpenAI] Loaded {len(NODE_CLASS_MAPPINGS)} nodes:")
for node_name in sorted(NODE_CLASS_MAPPINGS.keys()):
    print(f"  - {node_name}")

# Web directory for frontend extensions (if any)
WEB_DIRECTORY = "./web"

# Export for ComfyUI
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
