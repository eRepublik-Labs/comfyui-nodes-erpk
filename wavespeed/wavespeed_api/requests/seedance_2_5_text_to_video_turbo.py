# ABOUTME: Seedance 2.5 Turbo text-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the -turbo endpoint with identical payload.

from .seedance_2_5_text_to_video import Seedance25TextToVideo


class Seedance25TextToVideoTurbo(Seedance25TextToVideo):
    """Seedance 2.5 Turbo, same parameters, turbo endpoint."""

    def get_api_path(self):
        return "/api/v3/bytedance/seedance-2.5/text-to-video-turbo"
