# ABOUTME: Qwen Image 2512 text-to-image request for WaveSpeed AI.
# ABOUTME: Routes to the 2512 (7B model) endpoint with identical payload to the original.

from .qwen_image_text_to_image import QwenImageTextToImage


class QwenImageTextToImage2512(QwenImageTextToImage):
    """Qwen Image 2512 (7B model) — same parameters, different endpoint."""

    def get_api_path(self):
        return "/api/v3/wavespeed-ai/qwen-image/text-to-image-2512"
