# ABOUTME: ComfyUI node for background removal using rembg library.
# ABOUTME: Supports 14+ models including u2net, isnet, birefnet variants via ONNX.

"""
rembg Backend Node for ComfyUI

Uses the rembg library (ONNX Runtime) for background removal with 14+ model options.
"""

from typing import Dict, Any, Tuple, List
from tqdm import tqdm

from .utils import tensor_to_pil, pil_rgba_to_tensor, extract_mask_from_rgba

# Available rembg models with descriptions
REMBG_MODELS = [
    ("u2net", "General purpose (default)"),
    ("u2netp", "Lightweight, faster"),
    ("u2net_human_seg", "Human segmentation"),
    ("u2net_cloth_seg", "Clothing parsing"),
    ("silueta", "Compact u2net (43MB)"),
    ("isnet-general-use", "General purpose ISNet"),
    ("isnet-anime", "Anime characters"),
    ("sam", "Segment Anything Model"),
    ("birefnet-general", "BiRefNet general"),
    ("birefnet-general-lite", "BiRefNet lightweight"),
    ("birefnet-portrait", "BiRefNet portraits"),
    ("birefnet-dis", "BiRefNet dichotomous"),
    ("birefnet-hrsod", "BiRefNet high-res salient"),
    ("birefnet-cod", "BiRefNet camouflaged"),
    ("birefnet-massive", "BiRefNet massive dataset"),
]

# Model names for dropdown
MODEL_NAMES = [name for name, _ in REMBG_MODELS]


class RembgRemoveBackground:
    """
    Remove background using rembg library.

    Supports 14+ models optimized for different use cases.
    Uses ONNX Runtime for inference (CPU or GPU).
    """

    # Cache session to avoid reloading model
    _session = None
    _current_model = None

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "image": ("IMAGE",),
                "model": (MODEL_NAMES, {"default": "u2net"}),
            },
            "optional": {
                "alpha_matting": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Enable alpha matting for cleaner edges",
                    },
                ),
                "alpha_matting_foreground_threshold": (
                    "INT",
                    {
                        "default": 240,
                        "min": 0,
                        "max": 255,
                        "tooltip": "Foreground threshold for alpha matting",
                    },
                ),
                "alpha_matting_background_threshold": (
                    "INT",
                    {
                        "default": 10,
                        "min": 0,
                        "max": 255,
                        "tooltip": "Background threshold for alpha matting",
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "remove_background"
    CATEGORY = "ERPK/Background Removal"
    DESCRIPTION = "Remove background using rembg (ONNX). Supports 14+ models."

    @classmethod
    def _get_session(cls, model_name: str):
        """Get or create rembg session with model caching."""
        try:
            from rembg import new_session
        except ImportError:
            raise ImportError(
                "rembg is required. Install with: pip install rembg[gpu]"
            )

        if cls._session is None or cls._current_model != model_name:
            print(f"[BGRemoval] Loading rembg model: {model_name}")
            cls._session = new_session(model_name)
            cls._current_model = model_name

        return cls._session

    def remove_background(
        self,
        image,
        model: str,
        alpha_matting: bool = False,
        alpha_matting_foreground_threshold: int = 240,
        alpha_matting_background_threshold: int = 10,
    ) -> Tuple:
        """
        Remove background from images.

        Args:
            image: ComfyUI IMAGE tensor (B, H, W, C)
            model: rembg model name
            alpha_matting: Enable alpha matting refinement
            alpha_matting_foreground_threshold: Foreground threshold (0-255)
            alpha_matting_background_threshold: Background threshold (0-255)

        Returns:
            Tuple of (image_tensor, mask_tensor)
        """
        try:
            from rembg import remove
        except ImportError:
            raise ImportError(
                "rembg is required. Install with: pip install rembg[gpu]"
            )

        # Get cached session
        session = self._get_session(model)

        # Convert tensor to PIL images
        pil_images = tensor_to_pil(image)
        result_images: List = []

        # Process each image
        for pil_img in tqdm(pil_images, desc=f"[BGRemoval] rembg ({model})"):
            result = remove(
                pil_img,
                session=session,
                alpha_matting=alpha_matting,
                alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
                alpha_matting_background_threshold=alpha_matting_background_threshold,
            )
            result_images.append(result)

        # Convert back to tensors (RGBA for transparency support)
        image_tensor = pil_rgba_to_tensor(result_images)
        mask_tensor = extract_mask_from_rgba(result_images)

        return (image_tensor, mask_tensor)


# Node registration
NODE_CLASS_MAPPINGS = {
    "ERPK Remove Background (rembg)": RembgRemoveBackground,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ERPK Remove Background (rembg)": "Remove Background (rembg)",
}
