# ABOUTME: ERPK utility nodes for ComfyUI - string manipulation and general utilities.
# ABOUTME: Exports NODE_CLASS_MAPPINGS and NODE_DISPLAY_NAME_MAPPINGS for ComfyUI discovery.

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Import concat strings node
try:
    from .concat_strings import (
        NODE_CLASS_MAPPINGS as CONCAT_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as CONCAT_NODE_DISPLAY_NAME_MAPPINGS,
    )
    NODE_CLASS_MAPPINGS.update(CONCAT_NODE_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(CONCAT_NODE_DISPLAY_NAME_MAPPINGS)
except ImportError as e:
    print(f"[ERPK Utils] Warning: Could not load concat strings node: {e}")

print(f"[ERPK Utils] Loaded {len(NODE_CLASS_MAPPINGS)} nodes")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
