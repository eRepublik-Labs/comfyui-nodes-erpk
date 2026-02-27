# ABOUTME: Qwen Image Edit 2511 LoRA request for WaveSpeed AI.
# ABOUTME: Routes to the edit-2511-lora endpoint with identical payload to Edit Plus LoRA.

from .qwen_image_edit_plus_lora import QwenImageEditPlusLora


class QwenImageEdit2511Lora(QwenImageEditPlusLora):
    """Qwen Image Edit 2511 LoRA — multi-person editing with LoRA, same parameters as Edit Plus LoRA."""

    def get_api_path(self):
        return "/api/v3/wavespeed-ai/qwen-image/edit-2511-lora"
