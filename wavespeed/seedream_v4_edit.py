from .wavespeed_api.utils import imageurl2tensor
from .wavespeed_api.client import WaveSpeedClient
from .wavespeed_api.requests.seedream_v4_edit import SeedreamV4Edit


class SeedreamV4EditNode:
    """
    ByteDance Seedream V4 Edit Image Editor Node

    This node uses ByteDance's Seedream V4 Edit model to edit images based on text prompts.
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
                        "tooltip": "Text description of the desired image modifications",
                    },
                ),
                "images": (
                    "STRING",
                    {
                        "tooltip": "The images to edit. A maximum of 10 reference images can be uploaded.",
                    },
                ),
            },
            "optional": {
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
                "enable_sync_mode": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "If set to true, the function will wait for the result to be generated and uploaded before returning the response. It allows you to get the result directly in the response. This property is only available through the API.",
                    },
                ),
                "enable_base64_output": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "If enabled, the output will be encoded into a BASE64 string instead of a URL. This property is only available through the API.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)

    CATEGORY = "ERPK/WaveSpeedAI"
    FUNCTION = "execute"

    def execute(
        self,
        client,
        prompt,
        images,
        width=2048,
        height=2048,
        enable_sync_mode=False,
        enable_base64_output=False,
    ):
        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        if images is None or images == "":
            raise ValueError("Images must be provided")

        # Ensure we have at most 5 image URLs
        images_param = images[:10]

        request = SeedreamV4Edit(
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


NODE_CLASS_MAPPINGS = {"WaveSpeed Custom SeedreamV4Edit": SeedreamV4EditNode}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeed Custom SeedreamV4Edit": "Bytedance Seedream V4 Edit (Custom)"
}
