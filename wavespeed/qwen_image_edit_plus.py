from .wavespeed_api.utils import imageurl2tensor
from .wavespeed_api.client import WaveSpeedClient
from .wavespeed_api.requests.qwen_image_edit_plus import QwenImageEditPlus


class QwenImageEditPlusNode:
    """
    Qwen Image Edit Plus Node

    This node uses Qwen Image Edit Plus model for advanced image editing with multiple reference images.
    Accepts up to 3 reference images and supports bilingual (Chinese and English) text prompts.
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
                "images": (
                    "STRING",
                    {
                        "tooltip": "Reference images to edit. Maximum of 3 images can be provided (comma-separated URLs or paths)",
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
        images,
        width=1024,
        height=1024,
        seed=-1,
        output_format="jpeg",
        enable_sync_mode=False,
        enable_base64_output=False,
    ):
        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        if images is None or images == "":
            raise ValueError("Images must be provided")

        # Parse images input - support comma-separated URLs or array
        if isinstance(images, str):
            images_list = [img.strip() for img in images.split(",") if img.strip()]
        else:
            images_list = images

        # Ensure we have at most 3 images
        if len(images_list) > 3:
            raise ValueError("Maximum of 3 reference images can be uploaded")

        images_param = images_list[:3]

        size = f"{width}*{height}" if width and height else None

        request = QwenImageEditPlus(
            prompt=prompt,
            images=images_param,
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


NODE_CLASS_MAPPINGS = {"WaveSpeed Custom QwenImageEditPlus": QwenImageEditPlusNode}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeed Custom QwenImageEditPlus": "Qwen Image Edit Plus (Custom)"
}
