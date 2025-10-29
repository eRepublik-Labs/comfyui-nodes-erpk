# ABOUTME: Gemini ComfyUI Custom Nodes package initialization
# ABOUTME: Registers all Gemini nodes with ComfyUI

import os
import sys

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Initialize combined mappings
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Import and register all nodes
try:
    from .nodes import (
        NODE_CLASS_MAPPINGS as GEMINI_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as GEMINI_NODE_DISPLAY_NAME_MAPPINGS
    )
    NODE_CLASS_MAPPINGS.update(GEMINI_NODE_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(GEMINI_NODE_DISPLAY_NAME_MAPPINGS)
except ImportError as e:
    print(f"[Gemini] Warning: Could not load nodes: {e}")

# Print loaded nodes for debugging
print(f"[Gemini] Loaded {len(NODE_CLASS_MAPPINGS)} nodes:")
for node_name in sorted(NODE_CLASS_MAPPINGS.keys()):
    print(f"  - {node_name}")

# Web directory for frontend extensions (if any)
WEB_DIRECTORY = "./web"

# Export for ComfyUI
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
