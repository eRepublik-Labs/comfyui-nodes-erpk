# ABOUTME: ComfyUI nodes for background removal using BiRefNet via HuggingFace transformers.
# ABOUTME: Supports 15 model variants, dtype/device selection, local loading, and foreground refinement.

"""
BiRefNet Backend Nodes for ComfyUI

Uses BiRefNet directly via HuggingFace transformers.
Highest quality results, MIT licensed for commercial use.

Nodes:
- Remove Background (BiRefNet): Full background removal with all options
- Get Mask (BiRefNet): Mask-only output
- Foreground Refinement (BlurFusion): Clean foreground edges
"""

from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path
from tqdm import tqdm
import numpy as np
from PIL import Image

from .utils import tensor_to_pil, pil_rgba_to_tensor, pil_to_tensor, extract_mask_from_rgba

# All available BiRefNet variants on HuggingFace (15 models)
BIREFNET_VARIANTS = [
    # General purpose
    ("ZhengPeng7/BiRefNet", "General (default)"),
    ("ZhengPeng7/BiRefNet_HR", "General HR (2048x2048)"),
    ("ZhengPeng7/BiRefNet_T", "General Lite (fast)"),
    ("ZhengPeng7/BiRefNet_lite-2K", "General Lite 2K"),
    ("ZhengPeng7/BiRefNet_dynamic", "General Dynamic"),
    ("ZhengPeng7/BiRefNet_512x512", "General 512x512 (fastest)"),
    ("ZhengPeng7/BiRefNet-legacy", "General Legacy"),
    # Portrait
    ("ZhengPeng7/BiRefNet-portrait", "Portrait"),
    # Matting
    ("ZhengPeng7/BiRefNet-matting", "Matting"),
    ("ZhengPeng7/BiRefNet_HR-matting", "Matting HR"),
    ("ZhengPeng7/BiRefNet_lite-matting", "Matting Lite"),
    # Specialized detection
    ("ZhengPeng7/BiRefNet-DIS5K", "DIS (dichotomous)"),
    ("ZhengPeng7/BiRefNet-HRSOD", "HRSOD (salient object)"),
    ("ZhengPeng7/BiRefNet-COD", "COD (camouflaged)"),
    ("ZhengPeng7/BiRefNet-DIS5K-TR_TEs", "DIS Massive"),
]

VARIANT_NAMES = [name for name, _ in BIREFNET_VARIANTS]
VARIANT_DISPLAY = {name: display for name, display in BIREFNET_VARIANTS}

# Device options
DEVICE_OPTIONS = ["auto", "cuda", "cpu", "mps"]

# Dtype options
DTYPE_OPTIONS = ["float32", "float16"]

# Upscale methods for resizing
UPSCALE_METHODS = ["bilinear", "bicubic", "lanczos", "nearest", "nearest-exact", "area"]

# Map upscale method names to PIL resampling constants
UPSCALE_TO_PIL = {
    "bilinear": Image.Resampling.BILINEAR,
    "bicubic": Image.Resampling.BICUBIC,
    "lanczos": Image.Resampling.LANCZOS,
    "nearest": Image.Resampling.NEAREST,
    "nearest-exact": Image.Resampling.NEAREST,  # PIL uses NEAREST for both
    "area": Image.Resampling.BOX,  # PIL doesn't have AREA, BOX is closest
}


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return (0, 0, 0)
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        return (0, 0, 0)


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


def get_dtype(dtype_option: str):
    """Get torch dtype from string option."""
    import torch

    if dtype_option == "float16":
        return torch.float16
    return torch.float32


def get_comfyui_models_path() -> Path:
    """Get ComfyUI models directory path."""
    try:
        import folder_paths
        return Path(folder_paths.models_dir) / "BiRefNet"
    except ImportError:
        return Path("models") / "BiRefNet"


def list_local_models() -> List[str]:
    """List available local BiRefNet models."""
    models_path = get_comfyui_models_path()
    if not models_path.exists():
        return []

    models = []
    for ext in ["*.safetensors", "*.pth"]:
        models.extend([f.stem for f in models_path.glob(ext)])
    return sorted(models)


class BiRefNetRemoveBackground:
    """
    Remove background using BiRefNet via HuggingFace transformers.

    Features:
    - 15 model variants for different use cases
    - dtype selection (float16 for VRAM efficiency)
    - Device selection (auto/cuda/cpu/mps)
    - Configurable processing resolution with upscale method
    - Optional background color fill
    - Local model loading support
    - MIT licensed - safe for commercial use
    """

    # Cache models by (variant, device, dtype) key
    _models: Dict[str, Any] = {}

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        local_models = list_local_models()
        variant_choices = VARIANT_NAMES + ([f"local:{m}" for m in local_models] if local_models else [])

        return {
            "required": {
                "image": ("IMAGE",),
                "variant": (variant_choices, {"default": "ZhengPeng7/BiRefNet"}),
            },
            "optional": {
                "width": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 256,
                        "max": 2560,
                        "step": 64,
                        "tooltip": "Processing width. HR variants work best at 2048+, Lite variants at 512-1024.",
                    },
                ),
                "height": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 256,
                        "max": 2560,
                        "step": 64,
                        "tooltip": "Processing height. HR variants work best at 2048+, Lite variants at 512-1024.",
                    },
                ),
                "upscale_method": (
                    UPSCALE_METHODS,
                    {
                        "default": "bilinear",
                        "tooltip": "Interpolation method for resizing.",
                    },
                ),
                "device": (
                    DEVICE_OPTIONS,
                    {
                        "default": "auto",
                        "tooltip": "Processing device. Auto selects best available (CUDA > MPS > CPU).",
                    },
                ),
                "dtype": (
                    DTYPE_OPTIONS,
                    {
                        "default": "float32",
                        "tooltip": "Data type. float16 uses ~50% less VRAM but may have slight quality differences.",
                    },
                ),
                "fill_background": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Fill background with solid color instead of transparent.",
                    },
                ),
                "background_color": (
                    "STRING",
                    {
                        "default": "#000000",
                        "tooltip": "Hex color for background fill (e.g., #00FF00 for green).",
                    },
                ),
                "mask_threshold": (
                    "FLOAT",
                    {
                        "default": 0.0,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.001,
                        "tooltip": "Soft threshold for noise removal. Removes values below threshold while preserving gradients. Try 0.004 for noise removal.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "remove_background"
    CATEGORY = "ERPK/Background Removal"
    DESCRIPTION = "Remove background using BiRefNet. 15 model variants, dtype/device selection. MIT licensed."

    @classmethod
    def _get_model(cls, variant: str, device: str, dtype):
        """Get or create BiRefNet model with caching."""
        import torch
        from transformers import AutoModelForImageSegmentation

        cache_key = f"{variant}_{device}_{dtype}"

        if cache_key not in cls._models:
            # Check if it's a local model
            if variant.startswith("local:"):
                model_name = variant[6:]  # Remove "local:" prefix
                model_path = get_comfyui_models_path() / f"{model_name}.safetensors"
                if not model_path.exists():
                    model_path = get_comfyui_models_path() / f"{model_name}.pth"

                if not model_path.exists():
                    raise FileNotFoundError(f"Local model not found: {model_path}")

                print(f"[BGRemoval] Loading local BiRefNet: {model_path}")
                # Load from local safetensors/pth
                model = AutoModelForImageSegmentation.from_pretrained(
                    "ZhengPeng7/BiRefNet",  # Use default config
                    trust_remote_code=True,
                )
                # Load weights
                if model_path.suffix == ".safetensors":
                    from safetensors.torch import load_file
                    state_dict = load_file(str(model_path))
                else:
                    state_dict = torch.load(str(model_path), map_location="cpu")
                model.load_state_dict(state_dict, strict=False)
            else:
                print(f"[BGRemoval] Loading BiRefNet: {variant}")
                model = AutoModelForImageSegmentation.from_pretrained(
                    variant, trust_remote_code=True
                )

            # Move to device and set dtype
            model = model.to(device=device, dtype=dtype)
            model.eval()
            cls._models[cache_key] = model

            print(f"[BGRemoval] BiRefNet loaded on {device} ({dtype})")

        return cls._models[cache_key]

    def remove_background(
        self,
        image,
        variant: str,
        width: int = 1024,
        height: int = 1024,
        upscale_method: str = "bilinear",
        device: str = "auto",
        dtype: str = "float32",
        fill_background: bool = False,
        background_color: str = "#000000",
        mask_threshold: float = 0.0,
    ) -> Tuple:
        """Remove background from images using BiRefNet."""
        import torch
        from torchvision import transforms

        # Resolve device and dtype
        actual_device = get_device(device)
        actual_dtype = get_dtype(dtype)

        # Get cached model
        model = self._get_model(variant, actual_device, actual_dtype)

        # Get PIL resampling method
        resample_method = UPSCALE_TO_PIL.get(upscale_method, Image.Resampling.BILINEAR)

        # Preprocessing transform
        transform = transforms.Compose([
            transforms.Resize((height, width), interpolation=transforms.InterpolationMode.BILINEAR),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])

        # Convert tensor to PIL images
        pil_images = tensor_to_pil(image)
        result_images: List[Image.Image] = []
        result_masks: List[Image.Image] = []

        # Get background color if filling
        bg_color = hex_to_rgb(background_color) if fill_background else None

        # Process each image
        variant_short = variant.split("/")[-1] if "/" in variant else variant
        for pil_img in tqdm(pil_images, desc=f"[BGRemoval] BiRefNet ({variant_short})"):
            original_size = pil_img.size

            # Preprocess
            input_tensor = transform(pil_img).unsqueeze(0).to(device=actual_device, dtype=actual_dtype)

            # Inference
            with torch.no_grad():
                preds = model(input_tensor)[-1].sigmoid().cpu().float()

            # Post-process mask
            pred = preds[0].squeeze()

            # Apply soft threshold (removes noise while preserving gradients)
            if mask_threshold > 0:
                pred = pred * (pred > mask_threshold).float()

            mask_np = (pred.numpy() * 255).astype(np.uint8)
            mask_pil = Image.fromarray(mask_np, mode="L")

            # Resize mask back to original size using selected method
            mask_pil = mask_pil.resize(original_size, resample_method)
            result_masks.append(mask_pil)

            # Create output image
            if fill_background:
                # Solid color background
                background_img = Image.new("RGB", original_size, bg_color)
                background_img.paste(pil_img, mask=mask_pil)
                result_images.append(background_img)
            else:
                # Transparent RGBA
                rgba = pil_img.copy()
                rgba.putalpha(mask_pil)
                result_images.append(rgba)

        # Convert back to tensors
        if fill_background:
            image_tensor = pil_to_tensor(result_images)
        else:
            image_tensor = pil_rgba_to_tensor(result_images)

        mask_tensor = self._masks_to_tensor(result_masks)

        return (image_tensor, mask_tensor)

    def _masks_to_tensor(self, masks: List[Image.Image]):
        """Convert PIL masks to tensor."""
        import torch
        tensors = []
        for mask in masks:
            mask_np = np.array(mask).astype(np.float32) / 255.0
            tensors.append(torch.from_numpy(mask_np))
        return torch.stack(tensors)


class BiRefNetGetMask:
    """
    Get segmentation mask only using BiRefNet.

    Useful when you only need the mask for compositing or other operations.
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        local_models = list_local_models()
        variant_choices = VARIANT_NAMES + ([f"local:{m}" for m in local_models] if local_models else [])

        return {
            "required": {
                "image": ("IMAGE",),
                "variant": (variant_choices, {"default": "ZhengPeng7/BiRefNet"}),
            },
            "optional": {
                "width": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 256,
                        "max": 2560,
                        "step": 64,
                        "tooltip": "Processing width. HR variants work best at 2048+, Lite variants at 512-1024.",
                    },
                ),
                "height": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 256,
                        "max": 2560,
                        "step": 64,
                        "tooltip": "Processing height. HR variants work best at 2048+, Lite variants at 512-1024.",
                    },
                ),
                "upscale_method": (
                    UPSCALE_METHODS,
                    {
                        "default": "bilinear",
                        "tooltip": "Interpolation method for resizing.",
                    },
                ),
                "device": (DEVICE_OPTIONS, {"default": "auto"}),
                "dtype": (DTYPE_OPTIONS, {"default": "float32"}),
                "mask_threshold": (
                    "FLOAT",
                    {
                        "default": 0.0,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.001,
                        "tooltip": "Soft threshold for noise removal. Removes values below threshold while preserving gradients. Try 0.004 for noise removal.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("MASK",)
    RETURN_NAMES = ("mask",)
    FUNCTION = "get_mask"
    CATEGORY = "ERPK/Background Removal"
    DESCRIPTION = "Get segmentation mask using BiRefNet. Mask-only output for compositing."

    def get_mask(
        self,
        image,
        variant: str,
        width: int = 1024,
        height: int = 1024,
        upscale_method: str = "bilinear",
        device: str = "auto",
        dtype: str = "float32",
        mask_threshold: float = 0.0,
    ) -> Tuple:
        """Get mask from images using BiRefNet."""
        import torch
        from torchvision import transforms

        # Resolve device and dtype
        actual_device = get_device(device)
        actual_dtype = get_dtype(dtype)

        # Get cached model (reuse from main class)
        model = BiRefNetRemoveBackground._get_model(variant, actual_device, actual_dtype)

        # Get PIL resampling method
        resample_method = UPSCALE_TO_PIL.get(upscale_method, Image.Resampling.BILINEAR)

        # Preprocessing transform
        transform = transforms.Compose([
            transforms.Resize((height, width), interpolation=transforms.InterpolationMode.BILINEAR),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])

        # Convert tensor to PIL images
        pil_images = tensor_to_pil(image)
        masks = []

        # Process each image
        variant_short = variant.split("/")[-1] if "/" in variant else variant
        for pil_img in tqdm(pil_images, desc=f"[BGRemoval] BiRefNet Mask ({variant_short})"):
            original_size = pil_img.size

            # Preprocess
            input_tensor = transform(pil_img).unsqueeze(0).to(device=actual_device, dtype=actual_dtype)

            # Inference
            with torch.no_grad():
                preds = model(input_tensor)[-1].sigmoid().cpu().float()

            # Post-process mask
            pred = preds[0].squeeze()

            # Apply soft threshold (removes noise while preserving gradients)
            if mask_threshold > 0:
                pred = pred * (pred > mask_threshold).float()

            # Resize mask back to original size using selected method
            mask_np = pred.numpy()
            mask_pil = Image.fromarray((mask_np * 255).astype(np.uint8), mode="L")
            mask_pil = mask_pil.resize(original_size, resample_method)

            # Convert back to normalized tensor
            mask_resized = np.array(mask_pil).astype(np.float32) / 255.0
            masks.append(torch.from_numpy(mask_resized))

        return (torch.stack(masks),)


class BlurFusionForegroundEstimation:
    """
    Refine foreground edges using blur-based color estimation.

    Uses fast-foreground-estimation method to produce cleaner foregrounds
    by estimating true foreground colors at semi-transparent edges.
    Reduces color bleeding from background.

    Reference: https://github.com/Photoroom/fast-foreground-estimation
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "image": ("IMAGE",),
                "mask": ("MASK",),
            },
            "optional": {
                "blur_radius": (
                    "INT",
                    {
                        "default": 90,
                        "min": 1,
                        "max": 255,
                        "step": 1,
                        "tooltip": "Primary blur radius for foreground estimation.",
                    },
                ),
                "blur_radius_secondary": (
                    "INT",
                    {
                        "default": 6,
                        "min": 1,
                        "max": 255,
                        "step": 1,
                        "tooltip": "Secondary blur radius for edge refinement.",
                    },
                ),
                "fill_background": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Fill background with solid color instead of transparent.",
                    },
                ),
                "background_color": (
                    "STRING",
                    {
                        "default": "#000000",
                        "tooltip": "Hex color for background fill (e.g., #00FF00 for green).",
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "refine_foreground"
    CATEGORY = "ERPK/Background Removal"
    DESCRIPTION = "Refine foreground edges using blur-based color estimation. Reduces color bleeding."

    def refine_foreground(
        self,
        image,
        mask,
        blur_radius: int = 90,
        blur_radius_secondary: int = 6,
        fill_background: bool = False,
        background_color: str = "#000000",
    ) -> Tuple:
        """Refine foreground using blur fusion estimation."""
        import torch
        import cv2

        # Convert inputs
        pil_images = tensor_to_pil(image)

        # Handle mask dimensions
        if mask.dim() == 2:
            mask = mask.unsqueeze(0)

        result_images = []

        for i, pil_img in enumerate(tqdm(pil_images, desc="[BGRemoval] BlurFusion")):
            # Get corresponding mask
            mask_idx = min(i, mask.shape[0] - 1)
            mask_np = (mask[mask_idx].cpu().numpy() * 255).astype(np.uint8)

            # Resize mask if needed
            if mask_np.shape[:2] != (pil_img.height, pil_img.width):
                mask_np = cv2.resize(mask_np, (pil_img.width, pil_img.height), interpolation=cv2.INTER_LINEAR)

            # Convert image to numpy
            img_np = np.array(pil_img).astype(np.float32)

            # Estimate foreground using blur fusion
            foreground = self._blur_fusion_foreground(
                img_np, mask_np, blur_radius, blur_radius_secondary
            )

            # Create output
            if fill_background:
                # Parse hex color
                bg_rgb = hex_to_rgb(background_color)
                # Composite onto background
                alpha = mask_np.astype(np.float32) / 255.0
                alpha = alpha[:, :, np.newaxis]
                bg = np.full_like(foreground, bg_rgb, dtype=np.float32)
                result = foreground * alpha + bg * (1 - alpha)
                result_pil = Image.fromarray(result.astype(np.uint8), mode="RGB")
            else:
                # RGBA output
                result_pil = Image.fromarray(foreground.astype(np.uint8), mode="RGB")
                result_pil.putalpha(Image.fromarray(mask_np, mode="L"))

            result_images.append(result_pil)

        # Convert back to tensors
        if fill_background:
            image_tensor = pil_to_tensor(result_images)
        else:
            image_tensor = pil_rgba_to_tensor(result_images)

        # Return original mask
        return (image_tensor, mask)

    def _blur_fusion_foreground(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        blur_radius: int,
        blur_radius_secondary: int,
    ) -> np.ndarray:
        """
        Estimate foreground using blur fusion method.

        This reduces color bleeding at edges by estimating true foreground colors.
        """
        import cv2

        # Ensure odd kernel sizes
        blur_radius = blur_radius if blur_radius % 2 == 1 else blur_radius + 1
        blur_radius_secondary = blur_radius_secondary if blur_radius_secondary % 2 == 1 else blur_radius_secondary + 1

        # Normalize mask to 0-1
        alpha = mask.astype(np.float32) / 255.0
        alpha_3d = alpha[:, :, np.newaxis]

        # Blur the image weighted by alpha
        weighted_img = image * alpha_3d
        blurred_weighted = cv2.GaussianBlur(weighted_img, (blur_radius, blur_radius), 0)
        blurred_alpha = cv2.GaussianBlur(alpha, (blur_radius, blur_radius), 0)

        # Avoid division by zero
        blurred_alpha = np.maximum(blurred_alpha, 1e-6)

        # Estimate foreground
        foreground_estimate = blurred_weighted / blurred_alpha[:, :, np.newaxis]

        # Secondary refinement pass
        refined_weighted = foreground_estimate * alpha_3d
        blurred_refined = cv2.GaussianBlur(refined_weighted, (blur_radius_secondary, blur_radius_secondary), 0)
        blurred_alpha_secondary = cv2.GaussianBlur(alpha, (blur_radius_secondary, blur_radius_secondary), 0)
        blurred_alpha_secondary = np.maximum(blurred_alpha_secondary, 1e-6)

        foreground_refined = blurred_refined / blurred_alpha_secondary[:, :, np.newaxis]

        # Blend based on alpha
        # Use original image where alpha is high, estimated where alpha is low
        blend_factor = alpha_3d ** 2  # Quadratic blend for smoother transition
        result = image * blend_factor + foreground_refined * (1 - blend_factor)

        # Clip to valid range
        result = np.clip(result, 0, 255)

        return result


# Node registration
NODE_CLASS_MAPPINGS = {
    "ERPK Remove Background (BiRefNet)": BiRefNetRemoveBackground,
    "ERPK Get Mask (BiRefNet)": BiRefNetGetMask,
    "ERPK Foreground Refinement (BlurFusion)": BlurFusionForegroundEstimation,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ERPK Remove Background (BiRefNet)": "Remove Background (BiRefNet)",
    "ERPK Get Mask (BiRefNet)": "Get Mask (BiRefNet)",
    "ERPK Foreground Refinement (BlurFusion)": "Foreground Refinement (BlurFusion)",
}
