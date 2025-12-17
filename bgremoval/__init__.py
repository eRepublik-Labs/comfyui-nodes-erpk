# ABOUTME: Background removal nodes for ComfyUI with multiple backend support.
# ABOUTME: Supports rembg (14+ models), InSPyReNet, and BiRefNet backends.

"""
Background Removal ComfyUI Custom Nodes

This package provides ComfyUI nodes for background removal using multiple backends:
- rembg: ONNX-based, 14+ specialized models (u2net, isnet, birefnet variants, etc.)
- InSPyReNet: PyTorch-based via transparent-background package
- BiRefNet: Direct HuggingFace transformers integration for highest quality
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

# Import rembg backend nodes
try:
    from .rembg_node import (
        NODE_CLASS_MAPPINGS as REMBG_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as REMBG_NODE_DISPLAY_NAME_MAPPINGS,
    )
    NODE_CLASS_MAPPINGS.update(REMBG_NODE_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(REMBG_NODE_DISPLAY_NAME_MAPPINGS)
except ImportError as e:
    print(f"[BGRemoval] Warning: Could not load rembg nodes: {e}")

# Import InSPyReNet backend nodes
try:
    from .inspyrenet_node import (
        NODE_CLASS_MAPPINGS as INSPYRENET_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as INSPYRENET_NODE_DISPLAY_NAME_MAPPINGS,
    )
    NODE_CLASS_MAPPINGS.update(INSPYRENET_NODE_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(INSPYRENET_NODE_DISPLAY_NAME_MAPPINGS)
except ImportError as e:
    print(f"[BGRemoval] Warning: Could not load InSPyReNet nodes: {e}")

# Import BiRefNet backend nodes
try:
    from .birefnet_node import (
        NODE_CLASS_MAPPINGS as BIREFNET_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as BIREFNET_NODE_DISPLAY_NAME_MAPPINGS,
    )
    NODE_CLASS_MAPPINGS.update(BIREFNET_NODE_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(BIREFNET_NODE_DISPLAY_NAME_MAPPINGS)
except ImportError as e:
    print(f"[BGRemoval] Warning: Could not load BiRefNet nodes: {e}")

# Print loaded nodes for debugging
if NODE_CLASS_MAPPINGS:
    print(f"[BGRemoval] Loaded {len(NODE_CLASS_MAPPINGS)} nodes:")
    for node_name in NODE_CLASS_MAPPINGS.keys():
        print(f"  - {node_name}")
else:
    print("[BGRemoval] Warning: No background removal nodes loaded")

# Export for ComfyUI
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
