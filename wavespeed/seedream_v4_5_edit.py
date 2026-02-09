from .wavespeed_api.utils import imageurl2tensor
from .wavespeed_api.client import WaveSpeedClient
from .wavespeed_api.requests.seedream_v4_5_edit import SeedreamV4_5Edit
from .seedream_v4_5 import SEEDREAM_V4_5_SIZE_PRESETS


class SeedreamV4_5EditNode:
    """
    ByteDance Seedream V4.5 Edit Image Editor Node

    Enhanced typography and text rendering for editing images with text overlays.
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Text description of the desired image modifications",
                    },
                ),
                "image_url": (
                    "STRING",
                    {
                        "tooltip": "Image URL(s) to edit. Accepts single URL (string) or multiple URLs (array). Max 10 images.",
                    },
                ),
                "size_preset": (
                    list(SEEDREAM_V4_5_SIZE_PRESETS.keys()),
                    {
                        "default": "Custom",
                        "tooltip": "Recommended resolution presets. Select 'Custom' to use manual width/height.",
                    },
                ),
            },
            "optional": {
                "client": ("WAVESPEED_AI_API_CLIENT", {"tooltip": "WaveSpeed API client (optional if API key is configured in Settings)"}),
                "width": (
                    "INT",
                    {
                        "default": 2048,
                        "min": 1024,
                        "max": 4096,
                        "step": 8,
                        "display": "number",
                        "tooltip": "Custom width (only used when size_preset is 'Custom')",
                    },
                ),
                "height": (
                    "INT",
                    {
                        "default": 2048,
                        "min": 1024,
                        "max": 4096,
                        "step": 8,
                        "display": "number",
                        "tooltip": "Custom height (only used when size_preset is 'Custom')",
                    },
                ),
                "show_aspect_ratio": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Show aspect ratio in node title",
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

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)

    CATEGORY = "ERPK/WaveSpeedAI"
    FUNCTION = "execute"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    def execute(
        self,
        prompt,
        image_url,
        size_preset,
        client=None,
        width=2048,
        height=2048,
        show_aspect_ratio=True,
        enable_sync_mode=False,
        enable_base64_output=False,
    ):
        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient().create_client()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        if image_url is None or image_url == "":
            raise ValueError("Image URL must be provided")

        # Handle both single URL (string) and multiple URLs (list), max 10
        if isinstance(image_url, list):
            images_param = image_url[:10]
        else:
            images_param = [image_url]

        # Get dimensions from preset or use custom values
        preset_dims = SEEDREAM_V4_5_SIZE_PRESETS.get(size_preset)
        if preset_dims:
            width, height = preset_dims

        request = SeedreamV4_5Edit(
            prompt=prompt,
            images=images_param,
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
        return (images,)


NODE_CLASS_MAPPINGS = {"WaveSpeed Custom SeedreamV4_5Edit": SeedreamV4_5EditNode}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeed Custom SeedreamV4_5Edit": "Bytedance Seedream V4.5 Edit (Custom)"
}
