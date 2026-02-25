# ABOUTME: ComfyUI V3 node for background removal using InSPyReNet via transparent-background.
# ABOUTME: PyTorch-based, supports JIT compilation for faster inference. MIT licensed.

from comfy_api.latest import IO


class InSPyReNetRemoveBackground(IO.ComfyNode):
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

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="InSPyReNetRemoveBackground",
            display_name="Remove Background (InSPyReNet)",
            category="ERPK/Background Removal",
            description="Remove background using InSPyReNet (PyTorch). MIT licensed.",
            inputs=[
                IO.Image.Input("image"),
                IO.Boolean.Input("torchscript_jit", default=False, optional=True,
                                 tooltip="Enable TorchScript JIT for faster inference and lower memory"),
            ],
            outputs=[
                IO.Image.Output("image"),
                IO.Mask.Output("mask"),
            ],
        )

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

    @classmethod
    def execute(cls, image, torchscript_jit=False, **kwargs):
        from tqdm import tqdm
        from .utils import tensor_to_pil, pil_rgba_to_tensor, extract_mask_from_rgba

        # Get cached remover
        remover = cls._get_remover(torchscript_jit)

        # Convert tensor to PIL images
        pil_images = tensor_to_pil(image)
        result_images = []

        # Process each image
        jit_str = "JIT" if torchscript_jit else "default"
        for pil_img in tqdm(pil_images, desc=f"[BGRemoval] InSPyReNet ({jit_str})"):
            # transparent-background returns RGBA
            result = remover.process(pil_img, type="rgba")
            result_images.append(result)

        # Convert back to tensors (RGBA for transparency support)
        image_tensor = pil_rgba_to_tensor(result_images)
        mask_tensor = extract_mask_from_rgba(result_images)

        return IO.NodeOutput(image_tensor, mask_tensor)
