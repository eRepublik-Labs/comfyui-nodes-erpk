# ABOUTME: Background removal nodes for ComfyUI with multiple backend support.
# ABOUTME: Supports rembg (14+ models), InSPyReNet, BiRefNet, BEN2, and BlurFusion backends.

from .rembg_node import RembgRemoveBackground
from .inspyrenet_node import InSPyReNetRemoveBackground
from .birefnet_node import BiRefNetRemoveBackground, BiRefNetGetMask
from .blur_fusion_node import BlurFusionForegroundEstimation
from .ben2_node import BEN2RemoveBackground

NODES = [
    RembgRemoveBackground,
    InSPyReNetRemoveBackground,
    BiRefNetRemoveBackground,
    BiRefNetGetMask,
    BlurFusionForegroundEstimation,
    BEN2RemoveBackground,
]
__all__ = ["NODES"]
