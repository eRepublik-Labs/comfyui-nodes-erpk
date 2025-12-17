# ABOUTME: Apple ML models integration for ComfyUI.
# ABOUTME: Currently includes SHARP for single-image 3D Gaussian view synthesis.

"""
Apple ML Models - ComfyUI Custom Nodes

Integrates Apple's open-source ML models:
- SHARP: Single-image to 3D Gaussian splat view synthesis
"""

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Import SHARP nodes
try:
    from .sharp_nodes import (
        NODE_CLASS_MAPPINGS as SHARP_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as SHARP_NODE_DISPLAY_NAME_MAPPINGS,
    )

    NODE_CLASS_MAPPINGS.update(SHARP_NODE_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(SHARP_NODE_DISPLAY_NAME_MAPPINGS)
except ImportError as e:
    print(f"[Apple] Warning: Could not load SHARP nodes: {e}")
    print("[Apple] Install with: pip install git+https://github.com/apple/ml-sharp.git")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
