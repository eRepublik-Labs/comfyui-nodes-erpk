# ABOUTME: Seedance 2.0 Turbo text-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the -turbo endpoint with identical payload.

from .seedance_2_0_text_to_video import Seedance20TextToVideo


class Seedance20TextToVideoTurbo(Seedance20TextToVideo):
    """Seedance 2.0 Turbo — same parameters, turbo endpoint."""

    def get_api_path(self):
        return "/api/v3/bytedance/seedance-2.0/text-to-video-turbo"
