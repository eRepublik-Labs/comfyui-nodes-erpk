# ABOUTME: Seedance 2.0 Fast text-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the -fast endpoint with identical payload.

from .seedance_2_0_text_to_video import Seedance20TextToVideo


class Seedance20TextToVideoFast(Seedance20TextToVideo):
    """Seedance 2.0 Fast — same parameters, faster endpoint."""

    def get_api_path(self):
        return "/api/v3/bytedance/seedance-2.0-fast/text-to-video"
