# ABOUTME: Dreamina V3.1 text-to-image request for WaveSpeed AI.
# ABOUTME: Routes to the V3.1 endpoint with identical payload to V3.0.

from .dreamina_v3_text_to_image import DreaminaV3TextToImage


class DreaminaV3_1TextToImage(DreaminaV3TextToImage):
    """ByteDance Dreamina V3.1 — same parameters, different endpoint."""

    def get_api_path(self):
        return "/api/v3/bytedance/dreamina-v3.1/text-to-image"
