# ABOUTME: Seedance 2.0 Fast Turbo text-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the seedance-2.0-fast family text-to-video-turbo endpoint.

from .seedance_2_0_text_to_video import Seedance20TextToVideo


class Seedance20TextToVideoFastTurbo(Seedance20TextToVideo):
    """Seedance 2.0 Fast Turbo text-to-video — same parameters, fast-family turbo endpoint."""

    def get_api_path(self):
        return "/api/v3/bytedance/seedance-2.0-fast/text-to-video-turbo"
