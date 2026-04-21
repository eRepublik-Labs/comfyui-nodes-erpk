# ABOUTME: Qwen Image 2.0 Pro edit request for WaveSpeed AI.
# ABOUTME: Routes to the qwen-image-2.0-pro edit endpoint with identical payload.

from .qwen_image_2_0_edit import QwenImage20Edit


class QwenImage20ProEdit(QwenImage20Edit):
    """Qwen Image 2.0 Pro Edit — same parameters, different endpoint."""

    def get_api_path(self):
        return "/api/v3/wavespeed-ai/qwen-image-2.0-pro/edit"
