# ABOUTME: JibMix Qwen Image text-to-image request for WaveSpeed AI.
# ABOUTME: Portrait-optimized model using the same payload as Qwen Image.

from .qwen_image_text_to_image import QwenImageTextToImage


class JibMixQwenImage(QwenImageTextToImage):
    """JibMix Qwen Image — portrait-optimized model, same parameters as Qwen Image."""

    def get_api_path(self):
        return "/api/v3/wavespeed-ai/jib-mix-qwen-image/text-to-image"
