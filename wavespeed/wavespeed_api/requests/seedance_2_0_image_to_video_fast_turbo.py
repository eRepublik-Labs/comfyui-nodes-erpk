# ABOUTME: Seedance 2.0 Fast Turbo image-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the seedance-2.0-fast family image-to-video-turbo endpoint.

from .seedance_2_0_image_to_video import Seedance20ImageToVideo


class Seedance20ImageToVideoFastTurbo(Seedance20ImageToVideo):
    """Seedance 2.0 Fast Turbo image-to-video — same parameters, fast-family turbo endpoint."""

    def get_api_path(self):
        return "/api/v3/bytedance/seedance-2.0-fast/image-to-video-turbo"
