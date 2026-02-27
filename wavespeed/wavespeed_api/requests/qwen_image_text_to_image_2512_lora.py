# ABOUTME: Qwen Image 2512 LoRA text-to-image request for WaveSpeed AI.
# ABOUTME: Routes to the 2512 LoRA endpoint with identical payload to the original LoRA.

from .qwen_image_lora import QwenImageLora


class QwenImageTextToImage2512Lora(QwenImageLora):
    """Qwen Image 2512 LoRA (7B model) — same parameters as LoRA, different endpoint."""

    def get_api_path(self):
        return "/api/v3/wavespeed-ai/qwen-image/text-to-image-2512-lora"
