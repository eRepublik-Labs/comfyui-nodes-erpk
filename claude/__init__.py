"""
Claude ComfyUI Custom Nodes

Complete Claude API integration for ComfyUI including:
- Prompt enhancement with 50+ styles
- Text generation
- Vision analysis
- Multi-turn conversations
- Token counting utilities
"""

import os
import sys

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Initialize combined mappings
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Import and register core nodes
try:
    from .nodes import (
        NODE_CLASS_MAPPINGS as CORE_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as CORE_NODE_DISPLAY_NAME_MAPPINGS
    )
    NODE_CLASS_MAPPINGS.update(CORE_NODE_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(CORE_NODE_DISPLAY_NAME_MAPPINGS)
except ImportError as e:
    print(f"[Claude] Warning: Could not load core nodes: {e}")

# Import and register prompt enhancer node
try:
    from .prompt_enhancer import (
        NODE_CLASS_MAPPINGS as PROMPT_ENHANCER_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as PROMPT_ENHANCER_DISPLAY_MAPPINGS
    )
    NODE_CLASS_MAPPINGS.update(PROMPT_ENHANCER_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(PROMPT_ENHANCER_DISPLAY_MAPPINGS)
except ImportError as e:
    print(f"[Claude] Warning: Could not load prompt enhancer node: {e}")

# Import and register text generation node
try:
    from .text_generation import (
        NODE_CLASS_MAPPINGS as TEXT_GEN_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as TEXT_GEN_DISPLAY_MAPPINGS
    )
    NODE_CLASS_MAPPINGS.update(TEXT_GEN_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(TEXT_GEN_DISPLAY_MAPPINGS)
except ImportError as e:
    print(f"[Claude] Warning: Could not load text generation node: {e}")

# Import and register vision analysis node
try:
    from .vision_analysis import (
        NODE_CLASS_MAPPINGS as VISION_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as VISION_DISPLAY_MAPPINGS
    )
    NODE_CLASS_MAPPINGS.update(VISION_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(VISION_DISPLAY_MAPPINGS)
except ImportError as e:
    print(f"[Claude] Warning: Could not load vision analysis node: {e}")

# Import and register conversation nodes
try:
    from .conversation import (
        NODE_CLASS_MAPPINGS as CONVERSATION_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as CONVERSATION_DISPLAY_MAPPINGS
    )
    NODE_CLASS_MAPPINGS.update(CONVERSATION_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(CONVERSATION_DISPLAY_MAPPINGS)
except ImportError as e:
    print(f"[Claude] Warning: Could not load conversation nodes: {e}")

# Import and register token counter node
try:
    from .token_counter import (
        NODE_CLASS_MAPPINGS as TOKEN_COUNTER_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as TOKEN_COUNTER_DISPLAY_MAPPINGS
    )
    NODE_CLASS_MAPPINGS.update(TOKEN_COUNTER_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(TOKEN_COUNTER_DISPLAY_MAPPINGS)
except ImportError as e:
    print(f"[Claude] Warning: Could not load token counter node: {e}")

# Print loaded nodes for debugging
print(f"[Claude] Loaded {len(NODE_CLASS_MAPPINGS)} nodes:")
for node_name in sorted(NODE_CLASS_MAPPINGS.keys()):
    print(f"  - {node_name}")

# Web directory for frontend extensions (if any)
WEB_DIRECTORY = "./web"

# Export for ComfyUI
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
