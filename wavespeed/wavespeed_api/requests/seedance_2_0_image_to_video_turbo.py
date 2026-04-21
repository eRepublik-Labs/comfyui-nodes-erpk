# ABOUTME: Seedance 2.0 Turbo image-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the -turbo endpoint with identical payload.

from .seedance_2_0_image_to_video import Seedance20ImageToVideo


class Seedance20ImageToVideoTurbo(Seedance20ImageToVideo):
    """Seedance 2.0 Turbo Image-to-Video — same parameters, turbo endpoint."""

    def get_api_path(self):
        return "/api/v3/bytedance/seedance-2.0/image-to-video-turbo"
