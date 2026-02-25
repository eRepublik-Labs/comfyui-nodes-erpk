# ABOUTME: ComfyUI V3 node for background removal using rembg library.
# ABOUTME: Supports 14+ models including u2net, isnet, birefnet variants via ONNX.

from comfy_api.latest import IO

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


class RembgRemoveBackground(IO.ComfyNode):
    """
    Remove background using rembg library.

    Supports 14+ models optimized for different use cases.
    Uses ONNX Runtime for inference (CPU or GPU).
    """

    # Cache session to avoid reloading model
    _session = None
    _current_model = None

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="RembgRemoveBackground",
            display_name="Remove Background (rembg)",
            category="ERPK/Background Removal",
            description="Remove background using rembg (ONNX). Supports 14+ models.",
            inputs=[
                IO.Image.Input("image"),
                IO.Combo.Input("model", options=MODEL_NAMES, default="u2net"),
                IO.Boolean.Input("alpha_matting", default=False, optional=True,
                                 tooltip="Enable alpha matting for cleaner edges"),
                IO.Int.Input("alpha_matting_foreground_threshold", default=240,
                             min=0, max=255, optional=True,
                             tooltip="Foreground threshold for alpha matting"),
                IO.Int.Input("alpha_matting_background_threshold", default=10,
                             min=0, max=255, optional=True,
                             tooltip="Background threshold for alpha matting"),
            ],
            outputs=[
                IO.Image.Output("image"),
                IO.Mask.Output("mask"),
            ],
        )

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

    @classmethod
    def execute(
        cls,
        image,
        model="u2net",
        alpha_matting=False,
        alpha_matting_foreground_threshold=240,
        alpha_matting_background_threshold=10,
        **kwargs,
    ):
        from tqdm import tqdm
        from .utils import tensor_to_pil, pil_rgba_to_tensor, extract_mask_from_rgba

        try:
            from rembg import remove
        except ImportError:
            raise ImportError(
                "rembg is required. Install with: pip install rembg[gpu]"
            )

        # Get cached session
        session = cls._get_session(model)

        # Convert tensor to PIL images
        pil_images = tensor_to_pil(image)
        result_images = []

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

        return IO.NodeOutput(image_tensor, mask_tensor)
