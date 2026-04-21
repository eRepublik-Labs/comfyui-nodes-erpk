# ABOUTME: Qwen Image 2.0 Pro text-to-image request for WaveSpeed AI.
# ABOUTME: Routes to the qwen-image-2.0-pro text-to-image endpoint with identical payload.

from .qwen_image_2_0_text_to_image import QwenImage20TextToImage


class QwenImage20ProTextToImage(QwenImage20TextToImage):
    """Qwen Image 2.0 Pro — same parameters, different endpoint."""

    def get_api_path(self):
        return "/api/v3/wavespeed-ai/qwen-image-2.0-pro/text-to-image"
