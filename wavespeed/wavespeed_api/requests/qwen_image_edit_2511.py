# ABOUTME: Qwen Image Edit 2511 request for WaveSpeed AI.
# ABOUTME: Routes to the edit-2511 endpoint with identical payload to Edit Plus.

from .qwen_image_edit_plus import QwenImageEditPlus


class QwenImageEdit2511(QwenImageEditPlus):
    """Qwen Image Edit 2511 — multi-person editing, same parameters as Edit Plus."""

    def get_api_path(self):
        return "/api/v3/wavespeed-ai/qwen-image/edit-2511"
