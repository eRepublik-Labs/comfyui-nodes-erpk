# ABOUTME: ComfyUI node for background removal using BiRefNet via HuggingFace transformers.
# ABOUTME: Highest quality results, supports multiple variants including HR (2048x2048). MIT licensed.

"""
BiRefNet Backend Node for ComfyUI

Uses BiRefNet directly via HuggingFace transformers.
Highest quality results, MIT licensed for commercial use.
"""

from typing import Dict, Any, Tuple, List
from tqdm import tqdm
import numpy as np
from PIL import Image

from .utils import tensor_to_pil, pil_to_tensor, extract_mask_from_rgba, apply_mask_to_image

# Available BiRefNet variants on HuggingFace
BIREFNET_VARIANTS = [
    ("ZhengPeng7/BiRefNet", "BiRefNet (default)"),
    ("ZhengPeng7/BiRefNet_HR", "BiRefNet HR (2048x2048)"),
    ("ZhengPeng7/BiRefNet-matting", "BiRefNet Matting"),
    ("ZhengPeng7/BiRefNet_HR-matting", "BiRefNet HR Matting"),
    ("ZhengPeng7/BiRefNet-COD", "BiRefNet COD (camouflaged)"),
    ("ZhengPeng7/BiRefNet_512x512", "BiRefNet 512x512 (fast)"),
]

VARIANT_NAMES = [name for name, _ in BIREFNET_VARIANTS]
VARIANT_DISPLAY = {name: display for name, display in BIREFNET_VARIANTS}


class BiRefNetRemoveBackground:
    """
    Remove background using BiRefNet via HuggingFace transformers.

    Features:
    - Highest quality dichotomous image segmentation
    - Multiple variants for different use cases
    - HR variant supports 2048x2048 resolution
    - MIT licensed - safe for commercial use
    """

    # Cache model and processor
    _model = None
    _processor = None
    _current_variant = None

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "image": ("IMAGE",),
                "variant": (VARIANT_NAMES, {"default": "ZhengPeng7/BiRefNet"}),
            },
            "optional": {
                "resolution": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 256,
                        "max": 2048,
                        "step": 64,
                        "tooltip": "Processing resolution. HR variant can use 2048.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "remove_background"
    CATEGORY = "ERPK/Background Removal"
    DESCRIPTION = "Remove background using BiRefNet (HuggingFace). Highest quality. MIT licensed."

    @classmethod
    def _get_model(cls, variant: str):
        """Get or create BiRefNet model with caching."""
        try:
            import torch
            from transformers import AutoModelForImageSegmentation
            from torchvision import transforms
        except ImportError:
            raise ImportError(
                "transformers and torchvision are required. "
                "Install with: pip install transformers torchvision"
            )

        if cls._model is None or cls._current_variant != variant:
            print(f"[BGRemoval] Loading BiRefNet: {variant}")
            cls._model = AutoModelForImageSegmentation.from_pretrained(
                variant, trust_remote_code=True
            )

            # Move to GPU if available (CUDA or MPS for Mac)
            if torch.cuda.is_available():
                device = "cuda"
            elif torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
            cls._model = cls._model.to(device)
            cls._model.eval()
            cls._current_variant = variant

            print(f"[BGRemoval] BiRefNet loaded on {device}")

        return cls._model

    def remove_background(
        self,
        image,
        variant: str,
        resolution: int = 1024,
    ) -> Tuple:
        """
        Remove background from images using BiRefNet.

        Args:
            image: ComfyUI IMAGE tensor (B, H, W, C)
            variant: BiRefNet variant to use
            resolution: Processing resolution

        Returns:
            Tuple of (image_tensor, mask_tensor)
        """
        try:
            import torch
            from torchvision import transforms
        except ImportError:
            raise ImportError(
                "transformers and torchvision are required. "
                "Install with: pip install transformers torchvision"
            )

        # Get cached model
        model = self._get_model(variant)
        device = next(model.parameters()).device

        # Preprocessing transform
        transform = transforms.Compose([
            transforms.Resize((resolution, resolution)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])

        # Convert tensor to PIL images
        pil_images = tensor_to_pil(image)
        result_images: List = []

        # Process each image
        variant_short = variant.split("/")[-1]
        for pil_img in tqdm(pil_images, desc=f"[BGRemoval] BiRefNet ({variant_short})"):
            original_size = pil_img.size

            # Preprocess
            input_tensor = transform(pil_img).unsqueeze(0).to(device)

            # Inference
            with torch.no_grad():
                preds = model(input_tensor)[-1].sigmoid().cpu()

            # Post-process mask
            pred = preds[0].squeeze()
            mask_np = (pred.numpy() * 255).astype(np.uint8)
            mask_pil = Image.fromarray(mask_np, mode="L")

            # Resize mask back to original size
            mask_pil = mask_pil.resize(original_size, Image.Resampling.LANCZOS)

            # Apply mask to create RGBA
            rgba = pil_img.copy()
            rgba.putalpha(mask_pil)
            result_images.append(rgba)

        # Convert back to tensors
        image_tensor = pil_to_tensor(result_images)
        mask_tensor = extract_mask_from_rgba(result_images)

        return (image_tensor, mask_tensor)


# Node registration
NODE_CLASS_MAPPINGS = {
    "ERPK Remove Background (BiRefNet)": BiRefNetRemoveBackground,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ERPK Remove Background (BiRefNet)": "Remove Background (BiRefNet)",
}
