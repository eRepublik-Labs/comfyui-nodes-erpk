# ABOUTME: ComfyUI node for background removal using BEN2 (Background Erase Network 2).
# ABOUTME: Confidence-guided matting for accurate alpha mattes at edges. MIT licensed.

"""
BEN2 Backend Node for ComfyUI

Uses BEN2 (Background Erase Network 2) via HuggingFace hub.
Features confidence-guided matting (CGM) for accurate alpha mattes,
especially at fine details like hair and fur.

Install: pip install git+https://github.com/PramaLLC/BEN2.git
"""

from typing import Dict, Any, Tuple, List

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        return iterable

from .utils import tensor_to_pil, pil_rgba_to_tensor, extract_mask_from_rgba

# Device options (shared with birefnet_node)
DEVICE_OPTIONS = ["auto", "cuda", "cpu", "mps"]


def get_device(device_option: str) -> str:
    """Determine the device to use based on option and availability."""
    import torch

    if device_option == "auto":
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    return device_option


class BEN2RemoveBackground:
    """
    Remove background using BEN2 (Background Erase Network 2).

    Features:
    - Confidence-guided matting for accurate alpha mattes at edges
    - Built-in foreground refinement (blur fusion)
    - Handles resolution internally (1024x1024 processing)
    - Auto dtype: float16 on CUDA, float32 on CPU
    - MIT licensed - safe for commercial use
    """

    # Cache model by device key
    _model = None
    _current_device = None

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "refine_foreground": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Enable blur-fusion foreground refinement for cleaner edges. Slower but better for hair/fur.",
                    },
                ),
                "device": (
                    DEVICE_OPTIONS,
                    {
                        "default": "auto",
                        "tooltip": "Processing device. Auto selects best available (CUDA > MPS > CPU).",
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "remove_background"
    CATEGORY = "ERPK/Background Removal"
    DESCRIPTION = "Remove background using BEN2. Confidence-guided matting for accurate edges. MIT licensed."

    @classmethod
    def _get_model(cls, device: str):
        """Get or create BEN2 model with caching."""
        try:
            from ben2 import BEN_Base
        except ImportError:
            raise ImportError(
                "ben2 is required. Install with: pip install git+https://github.com/PramaLLC/BEN2.git"
            )

        if cls._model is None or cls._current_device != device:
            import torch

            print(f"[BGRemoval] Loading BEN2 on {device}")
            model = BEN_Base.from_pretrained("PramaLLC/BEN2")
            model.to(torch.device(device))
            model.eval()
            cls._model = model
            cls._current_device = device
            print(f"[BGRemoval] BEN2 loaded on {device}")

        return cls._model

    def remove_background(
        self,
        image,
        refine_foreground: bool = False,
        device: str = "auto",
    ) -> Tuple:
        """Remove background from images using BEN2."""
        # Resolve device
        actual_device = get_device(device)

        # Get cached model
        model = self._get_model(actual_device)

        # Convert tensor to PIL images
        pil_images = tensor_to_pil(image)
        result_images: List = []

        # Process each image
        refine_str = "refine" if refine_foreground else "default"
        for pil_img in tqdm(pil_images, desc=f"[BGRemoval] BEN2 ({refine_str})"):
            # BEN2 returns RGBA PIL image
            result = model.inference(pil_img, refine_foreground=refine_foreground)
            result_images.append(result)

        # Convert back to tensors
        image_tensor = pil_rgba_to_tensor(result_images)
        mask_tensor = extract_mask_from_rgba(result_images)

        return (image_tensor, mask_tensor)


# Node registration
NODE_CLASS_MAPPINGS = {
    "ERPK Remove Background (BEN2)": BEN2RemoveBackground,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ERPK Remove Background (BEN2)": "Remove Background (BEN2)",
}
