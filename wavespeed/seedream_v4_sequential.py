from .wavespeed_api.utils import imageurl2tensor
from .wavespeed_api.client import WaveSpeedClient
from .wavespeed_api.requests.seedream_v4_sequential import SeedreamV4Sequential


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
            },
            "optional": {
                "width": (
                    "INT",
                    {
                        "default": 2048,
                        "min": 1024,
                        "max": 4096,
                        "step": 8,
                        "display": "number",
                        "tooltip": "Image width (1024 to 4096)",
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
                        "tooltip": "Image height (1024 to 4096)",
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
    RETURN_NAMES = ("images",)

    CATEGORY = "ERPK/WaveSpeedAI"
    FUNCTION = "execute"

    def execute(
        self,
        client,
        prompt,
        max_images,
        width=2048,
        height=2048,
        enable_sync_mode=False,
        enable_base64_output=False,
    ):
        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        if max_images < 1 or max_images > 15:
            raise ValueError("max_images must be between 1 and 15")

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
        return (images,)


NODE_CLASS_MAPPINGS = {"WaveSpeed Custom SeedreamV4Sequential": SeedreamV4SequentialNode}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeed Custom SeedreamV4Sequential": "Bytedance Seedream V4 Sequential (Custom)"
}
