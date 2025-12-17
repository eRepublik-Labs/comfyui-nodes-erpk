# ABOUTME: ComfyUI nodes for Apple's SHARP model.
# ABOUTME: Converts single images to 3D Gaussian splats for novel view synthesis.

"""
SHARP Nodes for ComfyUI

SHARP (Single-image to 3D Gaussian) converts a single photograph into a
3D Gaussian splat representation that can be rendered from novel viewpoints.

Paper: https://machinelearning.apple.com/research/sharp
Code: https://github.com/apple/ml-sharp
"""

import os
import tempfile
from typing import Dict, Any, Tuple, List, Optional

import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F

# ComfyUI imports
import folder_paths


# Model URL from Apple CDN
SHARP_MODEL_URL = "https://ml-site.cdn-apple.com/models/sharp/sharp_2572gikvuh.pt"
SHARP_INTERNAL_RESOLUTION = 1536


class SHARPModelLoader:
    """Load and cache SHARP model."""

    _model = None
    _device = None

    @classmethod
    def get_model(cls, device: str = "auto"):
        """Get or load the SHARP model."""
        # Determine device
        if device == "auto":
            if torch.cuda.is_available():
                device = "cuda"
            elif torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"

        # Return cached model if device matches
        if cls._model is not None and cls._device == device:
            return cls._model, cls._device

        # Import sharp modules
        try:
            from sharp.models import create_predictor
            from sharp.models.params import PredictorParams
        except ImportError:
            raise ImportError(
                "SHARP is not installed. Install with:\n"
                "pip install git+https://github.com/apple/ml-sharp.git"
            )

        print(f"[SHARP] Loading model on {device}...")

        # Load checkpoint
        state_dict = torch.hub.load_state_dict_from_url(
            SHARP_MODEL_URL,
            map_location=device,
            weights_only=True,
        )

        # Create model with default params and load weights
        model = create_predictor(PredictorParams())
        model.load_state_dict(state_dict)
        model = model.to(device)
        model.eval()

        cls._model = model
        cls._device = device

        print(f"[SHARP] Model loaded successfully")
        return cls._model, cls._device


def tensor_to_numpy(tensor: torch.Tensor) -> np.ndarray:
    """Convert ComfyUI image tensor to numpy array."""
    # ComfyUI: (B, H, W, C) float [0,1]
    # Output: (H, W, C) uint8 [0,255]
    if tensor.dim() == 4:
        tensor = tensor[0]  # Take first image
    img_np = (tensor.cpu().numpy() * 255).astype(np.uint8)
    return img_np


def numpy_to_tensor(img_np: np.ndarray) -> torch.Tensor:
    """Convert numpy array to ComfyUI image tensor."""
    # Input: (H, W, C) uint8 [0,255]
    # Output: (1, H, W, C) float [0,1]
    tensor = torch.from_numpy(img_np.astype(np.float32) / 255.0)
    return tensor.unsqueeze(0)


class SHARPPredict:
    """
    Convert a single image to a 3D Gaussian splat (.ply file).

    Uses Apple's SHARP model to predict a 3D Gaussian representation
    from a single photograph in under one second on GPU.
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "focal_length_px": (
                    "FLOAT",
                    {
                        "default": 0.0,
                        "min": 0.0,
                        "max": 10000.0,
                        "step": 1.0,
                        "tooltip": "Focal length in pixels. 0 = auto-estimate from image width.",
                    },
                ),
                "output_dir": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Output directory for .ply file. Empty = ComfyUI output folder.",
                    },
                ),
                "filename_prefix": (
                    "STRING",
                    {
                        "default": "sharp",
                        "tooltip": "Prefix for output filename.",
                    },
                ),
                "device": (
                    ["auto", "cuda", "mps", "cpu"],
                    {"default": "auto"},
                ),
            },
        }

    RETURN_TYPES = ("STRING", "SHARP_GAUSSIANS")
    RETURN_NAMES = ("ply_path", "gaussians")
    FUNCTION = "predict"
    CATEGORY = "ERPK/Apple/SHARP"
    DESCRIPTION = "Convert a single image to 3D Gaussian splat (.ply file)"

    def predict(
        self,
        image: torch.Tensor,
        focal_length_px: float = 0.0,
        output_dir: str = "",
        filename_prefix: str = "sharp",
        device: str = "auto",
    ) -> Tuple[str, Any]:
        """Run SHARP prediction on input image."""
        try:
            from sharp.utils.gaussians import save_ply, unproject_gaussians
        except ImportError:
            raise ImportError(
                "SHARP is not installed. Install with:\n"
                "pip install git+https://github.com/apple/ml-sharp.git"
            )

        # Get model
        model, device = SHARPModelLoader.get_model(device)

        # Convert input image
        img_np = tensor_to_numpy(image)
        height, width = img_np.shape[:2]

        # Auto-estimate focal length if not provided
        if focal_length_px <= 0:
            focal_length_px = float(width)  # Common heuristic

        # Preprocess: normalize and resize
        img_tensor = torch.from_numpy(img_np).float() / 255.0
        img_tensor = img_tensor.permute(2, 0, 1).unsqueeze(0)  # (1, C, H, W)
        img_tensor = img_tensor.to(device)

        # Resize to internal resolution
        img_resized = F.interpolate(
            img_tensor,
            size=(SHARP_INTERNAL_RESOLUTION, SHARP_INTERNAL_RESOLUTION),
            mode="bilinear",
            align_corners=True,
        )

        # Compute disparity factor
        disparity_factor = torch.tensor(
            [focal_length_px / width], device=device, dtype=torch.float32
        )

        # Run inference
        with torch.no_grad():
            gaussians_ndc = model(img_resized, disparity_factor)

        # Build intrinsics matrix
        f_px = focal_length_px
        intrinsics = torch.tensor(
            [
                [f_px, 0, width / 2, 0],
                [0, f_px, height / 2, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1],
            ],
            dtype=torch.float32,
            device=device,
        )

        # Scale intrinsics to internal resolution
        intrinsics_resized = intrinsics.clone()
        intrinsics_resized[0] *= SHARP_INTERNAL_RESOLUTION / width
        intrinsics_resized[1] *= SHARP_INTERNAL_RESOLUTION / height

        # Unproject to metric space
        internal_shape = (SHARP_INTERNAL_RESOLUTION, SHARP_INTERNAL_RESOLUTION)
        extrinsics = torch.eye(4, dtype=torch.float32, device=device)
        gaussians = unproject_gaussians(
            gaussians_ndc, extrinsics, intrinsics_resized, internal_shape
        )

        # Determine output path
        if not output_dir:
            output_dir = folder_paths.get_output_directory()

        os.makedirs(output_dir, exist_ok=True)

        # Generate unique filename
        counter = 1
        while True:
            ply_filename = f"{filename_prefix}_{counter:05d}.ply"
            ply_path = os.path.join(output_dir, ply_filename)
            if not os.path.exists(ply_path):
                break
            counter += 1

        # Save PLY file
        save_ply(gaussians, focal_length_px, (height, width), ply_path)
        print(f"[SHARP] Saved: {ply_path}")

        return (ply_path, gaussians)


class SHARPRenderViews:
    """
    Render novel views from SHARP Gaussian splat.

    Renders the 3D Gaussian representation from multiple viewpoints
    to generate novel view images.

    Note: Requires CUDA for rendering.
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "ply_path": ("STRING", {"forceInput": True}),
                "num_views": (
                    "INT",
                    {
                        "default": 8,
                        "min": 1,
                        "max": 64,
                        "step": 1,
                        "tooltip": "Number of views to render around the scene.",
                    },
                ),
            },
            "optional": {
                "resolution": (
                    "INT",
                    {
                        "default": 512,
                        "min": 256,
                        "max": 2048,
                        "step": 64,
                        "tooltip": "Output image resolution.",
                    },
                ),
                "orbit_radius": (
                    "FLOAT",
                    {
                        "default": 0.3,
                        "min": 0.05,
                        "max": 2.0,
                        "step": 0.05,
                        "tooltip": "Camera orbit radius (distance from center).",
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "render_views"
    CATEGORY = "ERPK/Apple/SHARP"
    DESCRIPTION = "Render novel views from SHARP Gaussian splat (requires CUDA)"

    def render_views(
        self,
        ply_path: str,
        num_views: int = 8,
        resolution: int = 512,
        orbit_radius: float = 0.3,
    ) -> Tuple[torch.Tensor]:
        """Render multiple views from Gaussian splat."""
        if not torch.cuda.is_available():
            raise RuntimeError(
                "SHARP rendering requires CUDA. "
                "This node cannot run on CPU or MPS."
            )

        try:
            from sharp.utils.gaussians import load_ply
            from sharp.utils.camera import create_eye_trajectory, TrajectoryParams
            from sharp.cli.render import render_gaussians
        except ImportError:
            raise ImportError(
                "SHARP is not installed. Install with:\n"
                "pip install git+https://github.com/apple/ml-sharp.git"
            )

        # Load Gaussian splat
        gaussians, f_px, (height, width) = load_ply(ply_path)
        gaussians = gaussians.cuda()

        # Create camera trajectory
        trajectory_params = TrajectoryParams(
            radius=orbit_radius,
            num_frames=num_views,
        )
        trajectory = create_eye_trajectory(trajectory_params)

        # Render each view
        rendered_images = []
        for i, camera_pose in enumerate(trajectory):
            # Render frame
            result = render_gaussians(
                gaussians,
                camera_pose,
                f_px,
                (resolution, resolution),
            )
            # result["color"] is (H, W, 3) tensor
            rendered_images.append(result["color"].cpu())

        # Stack into batch tensor (B, H, W, C)
        images_tensor = torch.stack(rendered_images, dim=0)

        return (images_tensor,)


class SHARPRenderVideo:
    """
    Render orbit video from SHARP Gaussian splat.

    Creates an MP4 video showing the scene from a rotating camera.

    Note: Requires CUDA for rendering.
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "ply_path": ("STRING", {"forceInput": True}),
            },
            "optional": {
                "num_frames": (
                    "INT",
                    {
                        "default": 60,
                        "min": 10,
                        "max": 300,
                        "step": 10,
                        "tooltip": "Number of frames in the video.",
                    },
                ),
                "resolution": (
                    "INT",
                    {
                        "default": 512,
                        "min": 256,
                        "max": 2048,
                        "step": 64,
                        "tooltip": "Video resolution.",
                    },
                ),
                "fps": (
                    "INT",
                    {
                        "default": 30,
                        "min": 15,
                        "max": 60,
                        "step": 5,
                        "tooltip": "Frames per second.",
                    },
                ),
                "orbit_radius": (
                    "FLOAT",
                    {
                        "default": 0.3,
                        "min": 0.05,
                        "max": 2.0,
                        "step": 0.05,
                        "tooltip": "Camera orbit radius.",
                    },
                ),
                "output_dir": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Output directory. Empty = ComfyUI output folder.",
                    },
                ),
                "filename_prefix": (
                    "STRING",
                    {
                        "default": "sharp_video",
                        "tooltip": "Prefix for output filename.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "render_video"
    CATEGORY = "ERPK/Apple/SHARP"
    DESCRIPTION = "Render orbit video from SHARP Gaussian splat (requires CUDA)"

    def render_video(
        self,
        ply_path: str,
        num_frames: int = 60,
        resolution: int = 512,
        fps: int = 30,
        orbit_radius: float = 0.3,
        output_dir: str = "",
        filename_prefix: str = "sharp_video",
    ) -> Tuple[str]:
        """Render orbit video from Gaussian splat."""
        if not torch.cuda.is_available():
            raise RuntimeError(
                "SHARP video rendering requires CUDA. "
                "This node cannot run on CPU or MPS."
            )

        try:
            from sharp.utils.gaussians import load_ply
            from sharp.utils.camera import create_eye_trajectory, TrajectoryParams
            from sharp.cli.render import render_gaussians
            import imageio
        except ImportError:
            raise ImportError(
                "SHARP is not installed. Install with:\n"
                "pip install git+https://github.com/apple/ml-sharp.git"
            )

        # Load Gaussian splat
        gaussians, f_px, (height, width) = load_ply(ply_path)
        gaussians = gaussians.cuda()

        # Create camera trajectory
        trajectory_params = TrajectoryParams(
            radius=orbit_radius,
            num_frames=num_frames,
        )
        trajectory = create_eye_trajectory(trajectory_params)

        # Determine output path
        if not output_dir:
            output_dir = folder_paths.get_output_directory()

        os.makedirs(output_dir, exist_ok=True)

        # Generate unique filename
        counter = 1
        while True:
            video_filename = f"{filename_prefix}_{counter:05d}.mp4"
            video_path = os.path.join(output_dir, video_filename)
            if not os.path.exists(video_path):
                break
            counter += 1

        # Render and write video
        writer = imageio.get_writer(video_path, fps=fps)

        for i, camera_pose in enumerate(trajectory):
            # Render frame
            result = render_gaussians(
                gaussians,
                camera_pose,
                f_px,
                (resolution, resolution),
            )
            # Convert to uint8
            frame = (result["color"].cpu().numpy() * 255).astype(np.uint8)
            writer.append_data(frame)

            if (i + 1) % 10 == 0:
                print(f"[SHARP] Rendered frame {i + 1}/{num_frames}")

        writer.close()
        print(f"[SHARP] Saved video: {video_path}")

        return (video_path,)


# Node registration
NODE_CLASS_MAPPINGS = {
    "ERPK SHARP Predict": SHARPPredict,
    "ERPK SHARP Render Views": SHARPRenderViews,
    "ERPK SHARP Render Video": SHARPRenderVideo,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ERPK SHARP Predict": "SHARP Predict (Image to 3D Gaussian)",
    "ERPK SHARP Render Views": "SHARP Render Views",
    "ERPK SHARP Render Video": "SHARP Render Video",
}
