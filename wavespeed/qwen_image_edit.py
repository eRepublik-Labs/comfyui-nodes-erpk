from .wavespeed_api.utils import imageurl2tensor
from .wavespeed_api.client import WaveSpeedClient
from .wavespeed_api.requests.qwen_image_edit import QwenImageEdit


class QwenImageEditNode:
    """
    Qwen Image Edit Node

    This node uses Qwen Image Edit model to edit images based on text prompts.
    Supports both low-level visual appearance editing and high-level visual semantic editing,
    plus bilingual (Chinese and English) text editing capabilities.
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
                        "tooltip": "Text description of the desired image modifications (Chinese or English)",
                    },
                ),
                "image": (
                    "STRING",
                    {
                        "tooltip": "The image to edit (URL or path)",
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
        image,
        width=1024,
        height=1024,
        seed=-1,
        output_format="jpeg",
        enable_sync_mode=False,
        enable_base64_output=False,
    ):
        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        if image is None or image == "":
            raise ValueError("Image must be provided")

        size = f"{width}*{height}" if width and height else None

        request = QwenImageEdit(
            prompt=prompt,
            image=image,
            size=size,
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


NODE_CLASS_MAPPINGS = {"WaveSpeed Custom QwenImageEdit": QwenImageEditNode}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeed Custom QwenImageEdit": "Qwen Image Edit (Custom)"
}
