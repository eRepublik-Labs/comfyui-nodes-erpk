# ABOUTME: ERPK utility nodes for ComfyUI - string manipulation and general utilities.
# ABOUTME: Exports V3 node classes for registration via comfy_entrypoint.

from .concat_strings import ConcatenateStrings
from .seed import Seed

NODES = [ConcatenateStrings, Seed]

__all__ = ["NODES"]
