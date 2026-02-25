# ABOUTME: ComfyUI V3 node for background removal using BEN2 (Background Erase Network 2).
# ABOUTME: Confidence-guided matting for accurate alpha mattes at edges. MIT licensed.

from comfy_api.latest import IO

# Device options
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


class BEN2RemoveBackground(IO.ComfyNode):
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

    # HuggingFace repo for model code and weights
    HF_REPO_ID = "PramaLLC/BEN2"

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="BEN2RemoveBackground",
            display_name="Remove Background (BEN2)",
            category="ERPK/Background Removal",
            description="Remove background using BEN2. Confidence-guided matting for accurate edges. MIT licensed.",
            inputs=[
                IO.Image.Input("image"),
                IO.Boolean.Input("refine_foreground", default=False, optional=True,
                                 tooltip="Enable blur-fusion foreground refinement for cleaner edges. Slower but better for hair/fur."),
                IO.Combo.Input("device", options=DEVICE_OPTIONS, default="auto", optional=True,
                               tooltip="Processing device. Auto selects best available (CUDA > MPS > CPU)."),
            ],
            outputs=[
                IO.Image.Output("image"),
                IO.Mask.Output("mask"),
            ],
        )

    @classmethod
    def _load_ben2_class(cls):
        """Download and import BEN_Base class from HuggingFace."""
        import importlib.util
        from huggingface_hub import hf_hub_download

        model_code_path = hf_hub_download(cls.HF_REPO_ID, "BEN2.py")
        spec = importlib.util.spec_from_file_location("BEN2_model", model_code_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.BEN_Base

    @classmethod
    def _get_model(cls, device: str):
        """Get or create BEN2 model, downloading from HuggingFace if needed."""
        if cls._model is None or cls._current_device != device:
            import torch
            from huggingface_hub import hf_hub_download

            print(f"[BGRemoval] Loading BEN2 on {device}")

            BEN_Base = cls._load_ben2_class()
            model = BEN_Base()

            weights_path = hf_hub_download(cls.HF_REPO_ID, "BEN2_Base.pth")
            model.loadcheckpoints(weights_path)

            model.to(torch.device(device))
            model.train(False)
            cls._model = model
            cls._current_device = device
            print(f"[BGRemoval] BEN2 loaded on {device}")

        return cls._model

    @classmethod
    def execute(cls, image, refine_foreground=False, device="auto", **kwargs):
        from tqdm import tqdm
        from .utils import tensor_to_pil, pil_rgba_to_tensor, extract_mask_from_rgba

        # Resolve device
        actual_device = get_device(device)

        # Get cached model
        model = cls._get_model(actual_device)

        # Convert tensor to PIL images
        pil_images = tensor_to_pil(image)
        result_images = []

        # Process each image
        refine_str = "refine" if refine_foreground else "default"
        for pil_img in tqdm(pil_images, desc=f"[BGRemoval] BEN2 ({refine_str})"):
            # BEN2 returns RGBA PIL image
            result = model.inference(pil_img, refine_foreground=refine_foreground)
            result_images.append(result)

        # Convert back to tensors
        image_tensor = pil_rgba_to_tensor(result_images)
        mask_tensor = extract_mask_from_rgba(result_images)

        return IO.NodeOutput(image_tensor, mask_tensor)
