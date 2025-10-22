"""
WaveSpeed AI ComfyUI Custom Nodes

This package provides ComfyUI nodes for integrating WaveSpeed AI's API,
including ByteDance's Seedream V4 and Qwen Image models for text-to-image
and image editing capabilities.
"""

import os
import sys

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import node mappings from core nodes module
from .nodes import (
    NODE_CLASS_MAPPINGS as CORE_NODE_CLASS_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as CORE_NODE_DISPLAY_NAME_MAPPINGS
)

# Initialize combined mappings
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Add core nodes
NODE_CLASS_MAPPINGS.update(CORE_NODE_CLASS_MAPPINGS)
NODE_DISPLAY_NAME_MAPPINGS.update(CORE_NODE_DISPLAY_NAME_MAPPINGS)

# Import and register individual model nodes
try:
    # Seedream V4 nodes
    from .seedream_v4 import NODE_CLASS_MAPPINGS as SEEDREAM_V4_MAPPINGS
    from .seedream_v4 import NODE_DISPLAY_NAME_MAPPINGS as SEEDREAM_V4_DISPLAY_MAPPINGS
    NODE_CLASS_MAPPINGS.update(SEEDREAM_V4_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(SEEDREAM_V4_DISPLAY_MAPPINGS)
except ImportError as e:
    print(f"[WaveSpeed] Warning: Could not load Seedream V4 node: {e}")

try:
    from .seedream_v4_edit import NODE_CLASS_MAPPINGS as SEEDREAM_V4_EDIT_MAPPINGS
    from .seedream_v4_edit import NODE_DISPLAY_NAME_MAPPINGS as SEEDREAM_V4_EDIT_DISPLAY_MAPPINGS
    NODE_CLASS_MAPPINGS.update(SEEDREAM_V4_EDIT_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(SEEDREAM_V4_EDIT_DISPLAY_MAPPINGS)
except ImportError as e:
    print(f"[WaveSpeed] Warning: Could not load Seedream V4 Edit node: {e}")

try:
    from .seedream_v4_sequential import NODE_CLASS_MAPPINGS as SEEDREAM_V4_SEQ_MAPPINGS
    from .seedream_v4_sequential import NODE_DISPLAY_NAME_MAPPINGS as SEEDREAM_V4_SEQ_DISPLAY_MAPPINGS
    NODE_CLASS_MAPPINGS.update(SEEDREAM_V4_SEQ_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(SEEDREAM_V4_SEQ_DISPLAY_MAPPINGS)
except ImportError as e:
    print(f"[WaveSpeed] Warning: Could not load Seedream V4 Sequential node: {e}")

try:
    from .seedream_v4_edit_sequential import NODE_CLASS_MAPPINGS as SEEDREAM_V4_EDIT_SEQ_MAPPINGS
    from .seedream_v4_edit_sequential import NODE_DISPLAY_NAME_MAPPINGS as SEEDREAM_V4_EDIT_SEQ_DISPLAY_MAPPINGS
    NODE_CLASS_MAPPINGS.update(SEEDREAM_V4_EDIT_SEQ_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(SEEDREAM_V4_EDIT_SEQ_DISPLAY_MAPPINGS)
except ImportError as e:
    print(f"[WaveSpeed] Warning: Could not load Seedream V4 Edit Sequential node: {e}")

# Qwen Image nodes
try:
    from .qwen_image_text_to_image import NODE_CLASS_MAPPINGS as QWEN_T2I_MAPPINGS
    from .qwen_image_text_to_image import NODE_DISPLAY_NAME_MAPPINGS as QWEN_T2I_DISPLAY_MAPPINGS
    NODE_CLASS_MAPPINGS.update(QWEN_T2I_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(QWEN_T2I_DISPLAY_MAPPINGS)
except ImportError as e:
    print(f"[WaveSpeed] Warning: Could not load Qwen Image Text-to-Image node: {e}")

try:
    from .qwen_image_edit import NODE_CLASS_MAPPINGS as QWEN_EDIT_MAPPINGS
    from .qwen_image_edit import NODE_DISPLAY_NAME_MAPPINGS as QWEN_EDIT_DISPLAY_MAPPINGS
    NODE_CLASS_MAPPINGS.update(QWEN_EDIT_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(QWEN_EDIT_DISPLAY_MAPPINGS)
except ImportError as e:
    print(f"[WaveSpeed] Warning: Could not load Qwen Image Edit node: {e}")

try:
    from .qwen_image_edit_plus import NODE_CLASS_MAPPINGS as QWEN_EDIT_PLUS_MAPPINGS
    from .qwen_image_edit_plus import NODE_DISPLAY_NAME_MAPPINGS as QWEN_EDIT_PLUS_DISPLAY_MAPPINGS
    NODE_CLASS_MAPPINGS.update(QWEN_EDIT_PLUS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(QWEN_EDIT_PLUS_DISPLAY_MAPPINGS)
except ImportError as e:
    print(f"[WaveSpeed] Warning: Could not load Qwen Image Edit Plus node: {e}")

# Print loaded nodes for debugging
print(f"[WaveSpeed] Loaded {len(NODE_CLASS_MAPPINGS)} nodes:")
for node_name in NODE_CLASS_MAPPINGS.keys():
    print(f"  - {node_name}")

# Web directory for frontend extensions (if any)
WEB_DIRECTORY = "./web"

# Export for ComfyUI
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]