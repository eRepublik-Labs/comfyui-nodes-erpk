# ABOUTME: ComfyUI node for background removal using InSPyReNet via transparent-background.
# ABOUTME: PyTorch-based, supports JIT compilation for faster inference. MIT licensed.

"""
InSPyReNet Backend Node for ComfyUI

Uses the transparent-background package which wraps InSPyReNet.
PyTorch-based, runs on GPU, MIT licensed for commercial use.
"""

from typing import Dict, Any, Tuple, List
from tqdm import tqdm

from .utils import tensor_to_pil, pil_to_tensor, extract_mask_from_rgba


class InSPyReNetRemoveBackground:
    """
    Remove background using InSPyReNet via transparent-background.

    Features:
    - High-resolution salient object detection
    - Optional TorchScript JIT compilation for faster inference
    - MIT licensed - safe for commercial use
    """

    # Cache remover instance
    _remover = None
    _jit_enabled = None

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "torchscript_jit": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Enable TorchScript JIT for faster inference and lower memory",
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "remove_background"
    CATEGORY = "ERPK/Background Removal"
    DESCRIPTION = "Remove background using InSPyReNet (PyTorch). MIT licensed."

    @classmethod
    def _get_remover(cls, jit: bool):
        """Get or create Remover instance with caching."""
        try:
            from transparent_background import Remover
        except ImportError:
            raise ImportError(
                "transparent-background is required. Install with: pip install transparent-background"
            )

        if cls._remover is None or cls._jit_enabled != jit:
            print(f"[BGRemoval] Loading InSPyReNet (JIT={jit})")
            cls._remover = Remover(jit=jit)
            cls._jit_enabled = jit

        return cls._remover

    def remove_background(
        self,
        image,
        torchscript_jit: bool = False,
    ) -> Tuple:
        """
        Remove background from images using InSPyReNet.

        Args:
            image: ComfyUI IMAGE tensor (B, H, W, C)
            torchscript_jit: Enable JIT compilation for faster inference

        Returns:
            Tuple of (image_tensor, mask_tensor)
        """
        # Get cached remover
        remover = self._get_remover(torchscript_jit)

        # Convert tensor to PIL images
        pil_images = tensor_to_pil(image)
        result_images: List = []

        # Process each image
        jit_str = "JIT" if torchscript_jit else "default"
        for pil_img in tqdm(pil_images, desc=f"[BGRemoval] InSPyReNet ({jit_str})"):
            # transparent-background returns RGBA
            result = remover.process(pil_img, type="rgba")
            result_images.append(result)

        # Convert back to tensors
        image_tensor = pil_to_tensor(result_images)
        mask_tensor = extract_mask_from_rgba(result_images)

        return (image_tensor, mask_tensor)


# Node registration
NODE_CLASS_MAPPINGS = {
    "ERPK Remove Background (InSPyReNet)": InSPyReNetRemoveBackground,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ERPK Remove Background (InSPyReNet)": "Remove Background (InSPyReNet)",
}
