from .wavespeed_api.utils import imageurl2tensor
from .wavespeed_api.client import WaveSpeedClient
from .wavespeed_api.requests.seedream_v4 import SeedreamV4


class SeedreamV4Node:
    """
    ByteDance Seedream-V4 Image Generator Node

    This node uses ByteDance's Seedream-V4 model to generate high-quality images.
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
                        "tooltip": "Text description of the image to generate",
                    },
                ),
                "width": (
                    "INT",
                    {
                        "default": 2048,
                        "min": 0,
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
                        "min": 0,
                        "max": 4096,
                        "step": 8,
                        "display": "number",
                        "tooltip": "Image height (1024 to 4096)",
                    },
                ),
            },
            "optional": {},
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)

    CATEGORY = "ERPK/WaveSpeedAI"
    FUNCTION = "execute"

    def execute(
        self,
        client,
        prompt,
        width=1024,
        height=1024,
        seed=-1,
        guidance_scale=2.5,
    ):
        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        request = SeedreamV4(
            prompt=prompt,
            seed=seed,
            width=width,
            height=height,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = waveSpeedClient.send_request(request, True, 1)

        # Download and process images
        image_urls = response.get("outputs", [])
        if not image_urls:
            raise ValueError("No image URLs in the generated result")

        images = imageurl2tensor(image_urls)
        return (images,)


NODE_CLASS_MAPPINGS = {"WaveSpeed Custom SeedreamV4": SeedreamV4Node}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeed Custom SeedreamV4": "Bytedance Seedream V4 (Custom)"
}
