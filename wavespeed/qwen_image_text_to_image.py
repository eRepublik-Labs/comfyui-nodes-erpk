from .wavespeed_api.utils import imageurl2tensor
from .wavespeed_api.client import WaveSpeedClient
from .wavespeed_api.requests.qwen_image_text_to_image import QwenImageTextToImage


class QwenImageTextToImageNode:
    """
    Qwen Image Text-to-Image Generator Node

    This node uses Qwen Image model to generate high-quality images from text prompts.
    Supports bilingual (Chinese and English) prompts.
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
                        "tooltip": "Text description of the image to generate (Chinese or English)",
                    },
                ),
            },
            "optional": {
                "width": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 256,
                        "max": 1536,
                        "step": 8,
                        "display": "number",
                        "tooltip": "Image width (256 to 1536)",
                    },
                ),
                "height": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 256,
                        "max": 1536,
                        "step": 8,
                        "display": "number",
                        "tooltip": "Image height (256 to 1536)",
                    },
                ),
                "seed": (
                    "INT",
                    {
                        "default": -1,
                        "min": -1,
                        "max": 2147483647,
                        "tooltip": "Random seed for reproducibility (-1 for random)",
                    },
                ),
                "output_format": (
                    ["jpeg", "png", "webp"],
                    {
                        "default": "jpeg",
                        "tooltip": "Output image format",
                    },
                ),
                "enable_sync_mode": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Wait for completion before returning response",
                    },
                ),
                "enable_base64_output": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Return BASE64-encoded output instead of URL",
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
        width=1024,
        height=1024,
        seed=-1,
        output_format="jpeg",
        enable_sync_mode=False,
        enable_base64_output=False,
    ):
        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        request = QwenImageTextToImage(
            prompt=prompt,
            size=f"{width}*{height}",
            seed=seed,
            output_format=output_format,
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


NODE_CLASS_MAPPINGS = {"WaveSpeed Custom QwenImageT2I": QwenImageTextToImageNode}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeed Custom QwenImageT2I": "Qwen Image Text-to-Image (Custom)"
}
