# ABOUTME: Kling O3 Pro image-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the kling-video-o3-pro image-to-video endpoint with identical payload.

from .kling_o3_image_to_video import KlingO3ImageToVideo


class KlingO3ProImageToVideo(KlingO3ImageToVideo):
    """Kling O3 Pro image-to-video — same parameters, different endpoint."""

    def get_api_path(self):
        return "/api/v3/kwaivgi/kling-video-o3-pro/image-to-video"
