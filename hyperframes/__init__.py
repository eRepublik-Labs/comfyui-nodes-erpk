# ABOUTME: ERPK HyperFrames nodes - local HTML-to-video rendering via subprocess.
# ABOUTME: Exports V3 node classes that wrap the `hyperframes` npm CLI tool.

from .simple_composer import HyperFramesSimpleComposer
from .custom_template import HyperFramesCustomTemplate

NODES = [HyperFramesSimpleComposer, HyperFramesCustomTemplate]

__all__ = ["NODES"]
