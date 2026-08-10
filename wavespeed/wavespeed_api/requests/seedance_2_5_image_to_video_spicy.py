# ABOUTME: Seedance 2.5 Spicy image-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the -spicy endpoint with identical payload.

from .seedance_2_5_image_to_video import Seedance25ImageToVideo


class Seedance25ImageToVideoSpicy(Seedance25ImageToVideo):
    """Seedance 2.5 Spicy, same parameters, spicy endpoint."""

    def get_api_path(self):
        return "/api/v3/bytedance/seedance-2.5/image-to-video-spicy"
