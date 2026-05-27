# ABOUTME: ComfyUI V3 nodes for Apple's SHARP model.
# ABOUTME: Converts single images to 3D Gaussian splats for novel view synthesis.

"""
SHARP Nodes for ComfyUI

SHARP (Single-image to 3D Gaussian) converts a single photograph into a
3D Gaussian splat representation that can be rendered from novel viewpoints.

Paper: https://machinelearning.apple.com/research/sharp
Code: https://github.com/apple/ml-sharp
"""

from comfy_api.latest import IO

# Model URL from Apple CDN
SHARP_MODEL_URL = "https://ml-site.cdn-apple.com/models/sharp/sharp_2572gikvuh.pt"
SHARP_INTERNAL_RESOLUTION = 1536
DEVICE_OPTIONS = ["auto", "cuda", "mps", "cpu"]


def load_ply_fixed(path):
    """Load PLY with fix for SHARP's numpy/tensor bug in color conversion.

    SHARP's load_ply has a bug where it calls sRGB2linearRGB on numpy arrays
    but the function expects tensors. This wrapper fixes that.
    """
    import numpy as np
    import torch
    from pathlib import Path
    from plyfile import PlyData
    from sharp.utils.gaussians import Gaussians3D
    from sharp.utils import color_space as cs_utils

    ply_data = PlyData.read(Path(path))
    vertex_data = ply_data["vertex"]

    # Extract Gaussian parameters
    mean_vectors = np.stack([vertex_data["x"], vertex_data["y"], vertex_data["z"]], axis=-1)
    quaternions = np.stack(
        [vertex_data["rot_0"], vertex_data["rot_1"], vertex_data["rot_2"], vertex_data["rot_3"]],
        axis=-1,
    )
    scale_logits = np.stack(
        [vertex_data["scale_0"], vertex_data["scale_1"], vertex_data["scale_2"]], axis=-1
    )
    opacity_logits = vertex_data["opacity"]
    # f_dc values are degree-0 spherical harmonics, need conversion to RGB
    sh0 = np.stack([vertex_data["f_dc_0"], vertex_data["f_dc_1"], vertex_data["f_dc_2"]], axis=-1)
    coeff_degree0 = np.sqrt(1.0 / (4.0 * np.pi))
    colors = sh0 * coeff_degree0 + 0.5

    # Parse supplement data
    supplement_data = {}
    if "supplement" in ply_data:
        for prop in ply_data["supplement"].data.dtype.names:
            supplement_data[prop] = ply_data["supplement"][prop][0]

    # Get image dimensions
    height = int(supplement_data.get("height", 512))
    width = int(supplement_data.get("width", 512))
    focal_length_px = supplement_data.get("focal_length_px", np.array([width], dtype=np.float32))
    if isinstance(focal_length_px, np.ndarray):
        focal_length_px = focal_length_px.astype(np.float32)

    # Convert to tensors BEFORE color conversion (this is the fix)
    mean_vectors = torch.from_numpy(mean_vectors).view(1, -1, 3).float()
    quaternions = torch.from_numpy(quaternions).view(1, -1, 4).float()
    singular_values = torch.exp(torch.from_numpy(scale_logits).view(1, -1, 3)).float()
    opacities = torch.sigmoid(torch.from_numpy(opacity_logits).view(1, -1)).float()
    colors = torch.from_numpy(colors).view(1, -1, 3).float()

    # Now do color space conversion (with tensor, not numpy)
    color_space_index = supplement_data.get("color_space", 1)
    color_space = cs_utils.decode_color_space(color_space_index)
    if color_space == "sRGB":
        colors = cs_utils.sRGB2linearRGB(colors)

    gaussians = Gaussians3D(
        mean_vectors=mean_vectors,
        quaternions=quaternions,
        singular_values=singular_values,
        opacities=opacities,
        colors=colors,
    )

    f_px = float(focal_length_px[0]) if hasattr(focal_length_px, '__getitem__') else float(focal_length_px)
    return gaussians, f_px, (height, width)


class SHARPModelLoader:
    """Load and cache SHARP model."""

    _model = None
    _device = None

    @classmethod
    def get_model(cls, device="auto"):
        """Get or load the SHARP model."""
        import torch

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

        print("[SHARP] Model loaded successfully")
        return cls._model, cls._device


def tensor_to_numpy(tensor):
    """Convert ComfyUI image tensor to numpy array."""
    import numpy as np

    # ComfyUI: (B, H, W, C) float [0,1]
    # Output: (H, W, C) uint8 [0,255]
    if tensor.dim() == 4:
        tensor = tensor[0]  # Take first image
    img_np = (tensor.cpu().numpy() * 255).astype(np.uint8)
    return img_np


def numpy_to_tensor(img_np):
    """Convert numpy array to ComfyUI image tensor."""
    import numpy as np
    import torch

    # Input: (H, W, C) uint8 [0,255]
    # Output: (1, H, W, C) float [0,1]
    tensor = torch.from_numpy(img_np.astype(np.float32) / 255.0)
    return tensor.unsqueeze(0)


class SHARPPredict(IO.ComfyNode):
    """Convert a single image to a 3D Gaussian splat (.ply file)."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="SHARPPredict",
            display_name="SHARP Predict (Image to 3D Gaussian)",
            category="ERPK/Apple/SHARP",
            description="Convert a single image to 3D Gaussian splat (.ply file)",
            inputs=[
                IO.Image.Input("image"),
                IO.Float.Input("focal_length_px", optional=True, default=0.0,
                               min=0.0, max=10000.0, step=1.0,
                               tooltip="Focal length in pixels. 0 = auto-estimate from image width."),
                IO.String.Input("output_dir", optional=True, default="",
                                tooltip="Output directory for .ply file. Empty = ComfyUI output folder."),
                IO.String.Input("filename_prefix", optional=True, default="sharp",
                                tooltip="Prefix for output filename."),
                IO.Combo.Input("device", optional=True, options=DEVICE_OPTIONS, default="auto"),
            ],
            outputs=[
                IO.String.Output("ply_path"),
                IO.Custom("SHARP_GAUSSIANS").Output("gaussians"),
            ],
        )

    @classmethod
    def execute(cls, image, focal_length_px=0.0, output_dir="",
                filename_prefix="sharp", device="auto", **kwargs):
        import os
        import torch
        import torch.nn.functional as F
        import folder_paths

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
        from ..utils.safe_path import safe_filename_prefix
        safe_prefix = safe_filename_prefix(filename_prefix, default="sharp")
        counter = 1
        while True:
            ply_filename = f"{safe_prefix}_{counter:05d}.ply"
            ply_path = os.path.join(output_dir, ply_filename)
            if not os.path.exists(ply_path):
                break
            counter += 1

        # Save PLY file
        save_ply(gaussians, focal_length_px, (height, width), ply_path)
        print(f"[SHARP] Saved: {ply_path}")

        return IO.NodeOutput(ply_path, gaussians)


class SHARPRenderViews(IO.ComfyNode):
    """Render novel views from SHARP Gaussian splat (requires CUDA)."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="SHARPRenderViews",
            display_name="SHARP Render Views",
            category="ERPK/Apple/SHARP",
            description="Render novel views from SHARP Gaussian splat (requires CUDA)",
            inputs=[
                IO.String.Input("ply_path", force_input=True),
                IO.Int.Input("num_views", default=8, min=1, max=64, step=1,
                             tooltip="Number of views to render around the scene."),
                IO.Int.Input("resolution", optional=True, default=512,
                             min=256, max=2048, step=64,
                             tooltip="Output image resolution."),
                IO.Float.Input("max_disparity", optional=True, default=0.08,
                               min=0.01, max=0.5, step=0.01,
                               tooltip="Maximum camera disparity for view synthesis."),
            ],
            outputs=[
                IO.Image.Output("images"),
            ],
        )

    @classmethod
    def execute(cls, ply_path, num_views=8, resolution=512,
                max_disparity=0.08, **kwargs):
        import torch

        if not torch.cuda.is_available():
            raise RuntimeError(
                "SHARP rendering requires CUDA. "
                "This node cannot run on CPU or MPS."
            )

        try:
            from sharp.utils.camera import (
                create_eye_trajectory,
                create_camera_model,
                TrajectoryParams,
            )
            from sharp.utils.gsplat import GSplatRenderer
        except ImportError:
            raise ImportError(
                "SHARP is not installed. Install with:\n"
                "pip install git+https://github.com/apple/ml-sharp.git"
            )

        # Verify gsplat and CUDA are available
        try:
            import gsplat
            if not torch.cuda.is_available():
                raise RuntimeError(
                    "CUDA is not available. SHARP requires a CUDA-capable GPU."
                )
        except ImportError as e:
            raise RuntimeError(
                f"gsplat import error: {e}\n"
                "Install gsplat with: pip install gsplat"
            )

        # Load Gaussian splat
        gaussians, f_px, (height, width) = load_ply_fixed(ply_path)
        gaussians = gaussians.to(torch.device("cuda"))

        # Build 3x3 intrinsics matrix (standard pinhole camera format)
        # GSplatRenderer expects [B, 3, 3], CameraInfo returns (3, 3)
        cx, cy = resolution / 2, resolution / 2
        intrinsics = torch.tensor(
            [
                [f_px, 0, cx],
                [0, f_px, cy],
                [0, 0, 1],
            ],
            dtype=torch.float32,
            device="cuda",
        )

        # Create camera model (expects 3x3 intrinsics)
        camera_model = create_camera_model(
            gaussians,
            intrinsics,
            (resolution, resolution),
        )

        # Create camera trajectory
        trajectory_params = TrajectoryParams(
            max_disparity=max_disparity,
            num_steps=num_views,
        )
        eye_positions = create_eye_trajectory(
            gaussians,
            trajectory_params,
            (resolution, resolution),
            f_px,
        )

        # Create renderer
        renderer = GSplatRenderer()

        # Render each view
        rendered_images = []
        for eye_pos in eye_positions:
            # Compute camera parameters for this viewpoint
            # CameraInfo contains: intrinsics (3,3), extrinsics (4,4), width, height
            camera_info = camera_model.compute(eye_pos)

            # Render frame
            # GSplatRenderer.forward expects: extrinsics [B, 4, 4], intrinsics [B, 3, 3]
            # Note: SHARP's camera.compute() may return CPU tensors due to internal
            # torch.tensor() calls without device= arg, so we explicitly move to CUDA
            result = renderer.forward(
                gaussians,
                camera_info.extrinsics.unsqueeze(0).cuda(),
                camera_info.intrinsics.unsqueeze(0).cuda(),
                resolution,
                resolution,
            )
            # result.color is (1, C, H, W) tensor (PyTorch format)
            # Convert to (H, W, C) for ComfyUI
            rendered_images.append(result.color[0].permute(1, 2, 0).cpu())

        # Stack into batch tensor (B, H, W, C) for ComfyUI IMAGE format
        images_tensor = torch.stack(rendered_images, dim=0)

        from ..utils.inline_preview import inline_preview_image
        ui = inline_preview_image(cls, images_tensor, slot=0)
        return IO.NodeOutput(images_tensor, ui=ui)


class SHARPRenderVideo(IO.ComfyNode):
    """Render orbit video from SHARP Gaussian splat (requires CUDA)."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="SHARPRenderVideo",
            display_name="SHARP Render Video",
            category="ERPK/Apple/SHARP",
            description="Render orbit video from SHARP Gaussian splat (requires CUDA)",
            inputs=[
                IO.String.Input("ply_path", force_input=True),
                IO.Int.Input("num_frames", optional=True, default=60,
                             min=10, max=300, step=10,
                             tooltip="Number of frames in the video."),
                IO.Int.Input("resolution", optional=True, default=512,
                             min=256, max=2048, step=64,
                             tooltip="Video resolution."),
                IO.Int.Input("fps", optional=True, default=30,
                             min=15, max=60, step=5,
                             tooltip="Frames per second."),
                IO.Float.Input("max_disparity", optional=True, default=0.08,
                               min=0.01, max=0.5, step=0.01,
                               tooltip="Maximum camera disparity for view synthesis."),
                IO.String.Input("output_dir", optional=True, default="",
                                tooltip="Output directory. Empty = ComfyUI output folder."),
                IO.String.Input("filename_prefix", optional=True, default="sharp_video",
                                tooltip="Prefix for output filename."),
            ],
            outputs=[
                IO.String.Output("video_path"),
                IO.Image.Output("frames"),
            ],
        )

    @classmethod
    def execute(cls, ply_path, num_frames=60, resolution=512, fps=30,
                max_disparity=0.08, output_dir="", filename_prefix="sharp_video",
                **kwargs):
        import os
        import numpy as np
        import torch
        import folder_paths

        if not torch.cuda.is_available():
            raise RuntimeError(
                "SHARP video rendering requires CUDA. "
                "This node cannot run on CPU or MPS."
            )

        try:
            from sharp.utils.camera import (
                create_eye_trajectory,
                create_camera_model,
                TrajectoryParams,
            )
            from sharp.utils.gsplat import GSplatRenderer
            import imageio
        except ImportError:
            raise ImportError(
                "SHARP is not installed. Install with:\n"
                "pip install git+https://github.com/apple/ml-sharp.git"
            )

        # Verify gsplat and CUDA are available
        try:
            import gsplat
            if not torch.cuda.is_available():
                raise RuntimeError(
                    "CUDA is not available. SHARP requires a CUDA-capable GPU."
                )
        except ImportError as e:
            raise RuntimeError(
                f"gsplat import error: {e}\n"
                "Install gsplat with: pip install gsplat"
            )

        # Load Gaussian splat
        gaussians, f_px, (height, width) = load_ply_fixed(ply_path)
        gaussians = gaussians.to(torch.device("cuda"))

        # Build 3x3 intrinsics matrix (standard pinhole camera format)
        # GSplatRenderer expects [B, 3, 3], CameraInfo returns (3, 3)
        cx, cy = resolution / 2, resolution / 2
        intrinsics = torch.tensor(
            [
                [f_px, 0, cx],
                [0, f_px, cy],
                [0, 0, 1],
            ],
            dtype=torch.float32,
            device="cuda",
        )

        # Create camera model (expects 3x3 intrinsics)
        camera_model = create_camera_model(
            gaussians,
            intrinsics,
            (resolution, resolution),
        )

        # Create camera trajectory
        trajectory_params = TrajectoryParams(
            max_disparity=max_disparity,
            num_steps=num_frames,
        )
        eye_positions = create_eye_trajectory(
            gaussians,
            trajectory_params,
            (resolution, resolution),
            f_px,
        )

        # Determine output path
        if not output_dir:
            output_dir = folder_paths.get_output_directory()

        os.makedirs(output_dir, exist_ok=True)

        # Generate unique filename
        from ..utils.safe_path import safe_filename_prefix
        safe_prefix = safe_filename_prefix(filename_prefix, default="sharp_video")
        counter = 1
        while True:
            video_filename = f"{safe_prefix}_{counter:05d}.mp4"
            video_path = os.path.join(output_dir, video_filename)
            if not os.path.exists(video_path):
                break
            counter += 1

        # Create renderer
        renderer = GSplatRenderer()

        # Render and write video
        writer = imageio.get_writer(video_path, fps=fps)
        rendered_frames = []

        for i, eye_pos in enumerate(eye_positions):
            # Compute camera parameters for this viewpoint
            # CameraInfo contains: intrinsics (3,3), extrinsics (4,4), width, height
            camera_info = camera_model.compute(eye_pos)

            # Render frame
            # GSplatRenderer.forward expects: extrinsics [B, 4, 4], intrinsics [B, 3, 3]
            # Note: SHARP's camera.compute() may return CPU tensors due to internal
            # torch.tensor() calls without device= arg, so we explicitly move to CUDA
            result = renderer.forward(
                gaussians,
                camera_info.extrinsics.unsqueeze(0).cuda(),
                camera_info.intrinsics.unsqueeze(0).cuda(),
                resolution,
                resolution,
            )
            # Convert from (C, H, W) to (H, W, C) for ComfyUI IMAGE format
            frame_tensor = result.color[0].permute(1, 2, 0).cpu()
            rendered_frames.append(frame_tensor)

            # Convert to uint8 for video file
            frame_uint8 = (frame_tensor.numpy() * 255).astype(np.uint8)
            writer.append_data(frame_uint8)

            if (i + 1) % 10 == 0:
                print(f"[SHARP] Rendered frame {i + 1}/{num_frames}")

        writer.close()
        print(f"[SHARP] Saved video: {video_path}")

        # Stack frames into batch tensor (B, H, W, C) for ComfyUI IMAGE format
        frames_tensor = torch.stack(rendered_frames, dim=0)

        return IO.NodeOutput(video_path, frames_tensor)
