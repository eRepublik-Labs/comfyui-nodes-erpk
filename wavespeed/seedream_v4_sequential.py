from .wavespeed_api.utils import imageurl2tensor
from .wavespeed_api.client import WaveSpeedClient
from .wavespeed_api.requests.seedream_v4_sequential import SeedreamV4Sequential
from .seedream_v4 import SEEDREAM_V4_SIZE_PRESETS, calculate_aspect_ratio


class SeedreamV4SequentialNode:
    """
    ByteDance Seedream-V4 Sequential Image Generator Node

    This node uses ByteDance's Seedream-V4 Sequential model to generate multiple
    coherent images with cross-image consistency in a single pipeline.
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "client": ("WAVESPEED_AI_API_CLIENT",),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Text description for image generation. The node automatically appends the image count to your prompt.",
                    },
                ),
                "max_images": (
                    "INT",
                    {
                        "default": 4,
                        "min": 1,
                        "max": 15,
                        "step": 1,
                        "display": "number",
                        "tooltip": "Number of images to generate (1-15). Automatically added to prompt for API compliance.",
                    },
                ),
                "size_preset": (
                    list(SEEDREAM_V4_SIZE_PRESETS.keys()),
                    {
                        "default": "1:1 2K (1408x1408)",
                        "tooltip": "Recommended resolution presets. Select 'Custom' to use manual width/height.",
                    },
                ),
            },
            "optional": {
                "width": (
                    "INT",
                    {
                        "default": 1408,
                        "min": 320,
                        "max": 4096,
                        "step": 8,
                        "display": "number",
                        "tooltip": "Custom width (only used when size_preset is 'Custom')",
                    },
                ),
                "height": (
                    "INT",
                    {
                        "default": 1408,
                        "min": 320,
                        "max": 4096,
                        "step": 8,
                        "display": "number",
                        "tooltip": "Custom height (only used when size_preset is 'Custom')",
                    },
                ),
                "enable_sync_mode": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Wait for result generation before returning response",
                    },
                ),
                "enable_base64_output": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Return BASE64 encoded output instead of URLs",
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "aspect_ratio")

    CATEGORY = "ERPK/WaveSpeedAI"
    FUNCTION = "execute"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    def execute(
        self,
        client,
        prompt,
        max_images,
        size_preset,
        width=1408,
        height=1408,
        enable_sync_mode=False,
        enable_base64_output=False,
    ):
        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        if max_images < 1 or max_images > 15:
            raise ValueError("max_images must be between 1 and 15")

        # Get dimensions from preset or use custom values
        preset_dims = SEEDREAM_V4_SIZE_PRESETS.get(size_preset)
        if preset_dims:
            width, height = preset_dims

        aspect_ratio = calculate_aspect_ratio(width, height)

        generatePrompt = f"{prompt}. Generate a set of {max_images} consecutive."

        request = SeedreamV4Sequential(
            prompt=generatePrompt,
            max_images=max_images,
            size=f"{width}*{height}",
            enable_sync_mode=enable_sync_mode,
            enable_base64_output=enable_base64_output,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = waveSpeedClient.send_request(request, True, 1)

        # Download and process images
        image_urls = response.get("outputs", [])
        if not image_urls:
            raise ValueError("No image URLs in the generated result")

        images = imageurl2tensor(image_urls)
        return (images, aspect_ratio)


NODE_CLASS_MAPPINGS = {"WaveSpeed Custom SeedreamV4Sequential": SeedreamV4SequentialNode}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeed Custom SeedreamV4Sequential": "Bytedance Seedream V4 Sequential (Custom)"
}
