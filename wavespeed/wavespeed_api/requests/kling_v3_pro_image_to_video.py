# ABOUTME: Kling 3.0 Pro image-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the kling-v3.0-pro image-to-video endpoint with identical payload.

from .kling_v3_image_to_video import KlingV3ImageToVideo


class KlingV3ProImageToVideo(KlingV3ImageToVideo):
    """Kling 3.0 Pro image-to-video — same parameters, different endpoint."""

    def get_api_path(self):
        return "/api/v3/kwaivgi/kling-v3.0-pro/image-to-video"
