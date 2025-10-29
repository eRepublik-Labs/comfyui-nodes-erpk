"""
ERPK ComfyUI Custom Nodes

A collection of custom ComfyUI nodes from ERPK, including WaveSpeed AI, Claude API, and Gemini API integrations.
"""

# Initialize combined mappings
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Import and register WaveSpeed nodes
try:
    from .wavespeed import (
        NODE_CLASS_MAPPINGS as WAVESPEED_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as WAVESPEED_NODE_DISPLAY_NAME_MAPPINGS,
        WEB_DIRECTORY as WAVESPEED_WEB_DIRECTORY
    )
    NODE_CLASS_MAPPINGS.update(WAVESPEED_NODE_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(WAVESPEED_NODE_DISPLAY_NAME_MAPPINGS)
    WEB_DIRECTORY = WAVESPEED_WEB_DIRECTORY
except ImportError as e:
    print(f"[ERPK] Warning: Could not load WaveSpeed nodes: {e}")
    WEB_DIRECTORY = "./web"

# Import and register Claude nodes
try:
    from .claude import (
        NODE_CLASS_MAPPINGS as CLAUDE_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as CLAUDE_NODE_DISPLAY_NAME_MAPPINGS
    )
    NODE_CLASS_MAPPINGS.update(CLAUDE_NODE_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(CLAUDE_NODE_DISPLAY_NAME_MAPPINGS)
except ImportError as e:
    print(f"[ERPK] Warning: Could not load Claude nodes: {e}")

# Import and register Gemini nodes
try:
    from .gemini import (
        NODE_CLASS_MAPPINGS as GEMINI_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as GEMINI_NODE_DISPLAY_NAME_MAPPINGS
    )
    NODE_CLASS_MAPPINGS.update(GEMINI_NODE_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(GEMINI_NODE_DISPLAY_NAME_MAPPINGS)
except ImportError as e:
    print(f"[ERPK] Warning: Could not load Gemini nodes: {e}")

# Print loaded nodes summary
print(f"[ERPK] Loaded {len(NODE_CLASS_MAPPINGS)} total nodes")

# Export for ComfyUI
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
