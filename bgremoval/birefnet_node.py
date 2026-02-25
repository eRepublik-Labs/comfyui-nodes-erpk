# ABOUTME: ComfyUI V3 nodes for background removal using BiRefNet via HuggingFace transformers.
# ABOUTME: Supports 17 model variants, dtype/device selection, local loading, and mask extraction.

from typing import Tuple
from pathlib import Path

from comfy_api.latest import IO

# All available BiRefNet variants on HuggingFace (17 models)
BIREFNET_VARIANTS = [
    # General purpose
    ("ZhengPeng7/BiRefNet", "General (default)"),
    ("ZhengPeng7/BiRefNet_HR", "General HR (2048x2048)"),
    ("ZhengPeng7/BiRefNet_T", "General Lite (fast)"),
    ("ZhengPeng7/BiRefNet_lite", "General Lite (44M params)"),
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
    ("ZhengPeng7/BiRefNet_dynamic-matting", "Matting Dynamic"),
    # Specialized detection
    ("ZhengPeng7/BiRefNet-DIS5K", "DIS (dichotomous)"),
    ("ZhengPeng7/BiRefNet-HRSOD", "HRSOD (salient object)"),
    ("ZhengPeng7/BiRefNet-COD", "COD (camouflaged)"),
    ("ZhengPeng7/BiRefNet-DIS5K-TR_TEs", "DIS Massive"),
]

VARIANT_NAMES = [name for name, _ in BIREFNET_VARIANTS]

# Device and dtype options
DEVICE_OPTIONS = ["auto", "cuda", "cpu", "mps"]
DTYPE_OPTIONS = ["float32", "float16"]

# Upscale method names for dropdown
UPSCALE_METHODS = ["bilinear", "bicubic", "lanczos", "nearest", "nearest-exact", "area"]


def _get_upscale_to_pil():
    """Build PIL resampling constant map lazily to avoid module-level PIL import."""
    from PIL import Image
    return {
        "bilinear": Image.Resampling.BILINEAR,
        "bicubic": Image.Resampling.BICUBIC,
        "lanczos": Image.Resampling.LANCZOS,
        "nearest": Image.Resampling.NEAREST,
        "nearest-exact": Image.Resampling.NEAREST,
        "area": Image.Resampling.BOX,
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


def list_local_models():
    """List available local BiRefNet models."""
    models_path = get_comfyui_models_path()
    if not models_path.exists():
        return []

    models = []
    for ext in ["*.safetensors", "*.pth"]:
        models.extend([f.stem for f in models_path.glob(ext)])
    return sorted(models)


class BiRefNetRemoveBackground(IO.ComfyNode):
    """
    Remove background using BiRefNet via HuggingFace transformers.

    Features:
    - 17 model variants for different use cases
    - dtype selection (float16 for VRAM efficiency)
    - Device selection (auto/cuda/cpu/mps)
    - Configurable processing resolution with upscale method
    - Optional background color fill
    - Local model loading support
    - MIT licensed - safe for commercial use
    """

    # Cache models by (variant, device, dtype) key
    _models = {}

    @classmethod
    def define_schema(cls):
        local_models = list_local_models()
        variant_choices = VARIANT_NAMES + ([f"local:{m}" for m in local_models] if local_models else [])

        return IO.Schema(
            node_id="BiRefNetRemoveBackground",
            display_name="Remove Background (BiRefNet)",
            category="ERPK/Background Removal",
            description="Remove background using BiRefNet. 17 model variants, dtype/device selection. MIT licensed.",
            inputs=[
                IO.Image.Input("image"),
                IO.Combo.Input("variant", options=variant_choices, default="ZhengPeng7/BiRefNet"),
                IO.Int.Input("width", default=1024, min=256, max=2560, step=64, optional=True,
                             tooltip="Processing width. HR variants work best at 2048+, Lite variants at 512-1024."),
                IO.Int.Input("height", default=1024, min=256, max=2560, step=64, optional=True,
                             tooltip="Processing height. HR variants work best at 2048+, Lite variants at 512-1024."),
                IO.Combo.Input("upscale_method", options=UPSCALE_METHODS, default="bilinear", optional=True,
                               tooltip="Interpolation method for resizing."),
                IO.Combo.Input("device", options=DEVICE_OPTIONS, default="auto", optional=True,
                               tooltip="Processing device. Auto selects best available (CUDA > MPS > CPU)."),
                IO.Combo.Input("dtype", options=DTYPE_OPTIONS, default="float32", optional=True,
                               tooltip="Data type. float16 uses ~50% less VRAM but may have slight quality differences."),
                IO.Boolean.Input("fill_background", default=False, optional=True,
                                 tooltip="Fill background with solid color instead of transparent."),
                IO.String.Input("background_color", default="#000000", optional=True,
                                tooltip="Hex color for background fill (e.g., #00FF00 for green)."),
                IO.Float.Input("mask_threshold", default=0.0, min=0.0, max=1.0, step=0.001, optional=True,
                               tooltip="Soft threshold for noise removal. Removes values below threshold while preserving gradients. Try 0.004 for noise removal."),
            ],
            outputs=[
                IO.Image.Output("image"),
                IO.Mask.Output("mask"),
            ],
        )

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
            model.train(False)
            cls._models[cache_key] = model

            print(f"[BGRemoval] BiRefNet loaded on {device} ({dtype})")

        return cls._models[cache_key]

    @classmethod
    def execute(
        cls,
        image,
        variant="ZhengPeng7/BiRefNet",
        width=1024,
        height=1024,
        upscale_method="bilinear",
        device="auto",
        dtype="float32",
        fill_background=False,
        background_color="#000000",
        mask_threshold=0.0,
        **kwargs,
    ):
        import numpy as np
        import torch
        from PIL import Image
        from torchvision import transforms
        from tqdm import tqdm
        from .utils import tensor_to_pil, pil_rgba_to_tensor, pil_to_tensor

        upscale_to_pil = _get_upscale_to_pil()

        # Resolve device and dtype
        actual_device = get_device(device)
        actual_dtype = get_dtype(dtype)

        # Get cached model
        model = cls._get_model(variant, actual_device, actual_dtype)

        # Get PIL resampling method
        resample_method = upscale_to_pil.get(upscale_method, Image.Resampling.BILINEAR)

        # Preprocessing transform
        transform = transforms.Compose([
            transforms.Resize((height, width), interpolation=transforms.InterpolationMode.BILINEAR),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])

        # Convert tensor to PIL images
        pil_images = tensor_to_pil(image)
        result_images = []
        result_masks = []

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

        mask_tensor = _masks_to_tensor(result_masks)

        return IO.NodeOutput(image_tensor, mask_tensor)


class BiRefNetGetMask(IO.ComfyNode):
    """
    Get segmentation mask only using BiRefNet.

    Useful when you only need the mask for compositing or other operations.
    """

    @classmethod
    def define_schema(cls):
        local_models = list_local_models()
        variant_choices = VARIANT_NAMES + ([f"local:{m}" for m in local_models] if local_models else [])

        return IO.Schema(
            node_id="BiRefNetGetMask",
            display_name="Get Mask (BiRefNet)",
            category="ERPK/Background Removal",
            description="Get segmentation mask using BiRefNet. Mask-only output for compositing.",
            inputs=[
                IO.Image.Input("image"),
                IO.Combo.Input("variant", options=variant_choices, default="ZhengPeng7/BiRefNet"),
                IO.Int.Input("width", default=1024, min=256, max=2560, step=64, optional=True,
                             tooltip="Processing width. HR variants work best at 2048+, Lite variants at 512-1024."),
                IO.Int.Input("height", default=1024, min=256, max=2560, step=64, optional=True,
                             tooltip="Processing height. HR variants work best at 2048+, Lite variants at 512-1024."),
                IO.Combo.Input("upscale_method", options=UPSCALE_METHODS, default="bilinear", optional=True,
                               tooltip="Interpolation method for resizing."),
                IO.Combo.Input("device", options=DEVICE_OPTIONS, default="auto", optional=True,
                               tooltip="Processing device. Auto selects best available (CUDA > MPS > CPU)."),
                IO.Combo.Input("dtype", options=DTYPE_OPTIONS, default="float32", optional=True,
                               tooltip="Data type. float16 uses ~50% less VRAM but may have slight quality differences."),
                IO.Float.Input("mask_threshold", default=0.0, min=0.0, max=1.0, step=0.001, optional=True,
                               tooltip="Soft threshold for noise removal. Removes values below threshold while preserving gradients. Try 0.004 for noise removal."),
            ],
            outputs=[
                IO.Mask.Output("mask"),
            ],
        )

    @classmethod
    def execute(
        cls,
        image,
        variant="ZhengPeng7/BiRefNet",
        width=1024,
        height=1024,
        upscale_method="bilinear",
        device="auto",
        dtype="float32",
        mask_threshold=0.0,
        **kwargs,
    ):
        import numpy as np
        import torch
        from PIL import Image
        from torchvision import transforms
        from tqdm import tqdm
        from .utils import tensor_to_pil

        upscale_to_pil = _get_upscale_to_pil()

        # Resolve device and dtype
        actual_device = get_device(device)
        actual_dtype = get_dtype(dtype)

        # Get cached model (reuse from BiRefNetRemoveBackground)
        model = BiRefNetRemoveBackground._get_model(variant, actual_device, actual_dtype)

        # Get PIL resampling method
        resample_method = upscale_to_pil.get(upscale_method, Image.Resampling.BILINEAR)

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

        return IO.NodeOutput(torch.stack(masks))


def _masks_to_tensor(masks):
    """Convert PIL masks to tensor."""
    import numpy as np
    import torch
    tensors = []
    for mask in masks:
        mask_np = np.array(mask).astype(np.float32) / 255.0
        tensors.append(torch.from_numpy(mask_np))
    return torch.stack(tensors)
