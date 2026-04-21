# ABOUTME: Kling O3 Pro text-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the kling-video-o3-pro text-to-video endpoint with identical payload.

from .kling_o3_text_to_video import KlingO3TextToVideo


class KlingO3ProTextToVideo(KlingO3TextToVideo):
    """Kling O3 Pro text-to-video — same parameters, different endpoint."""

    def get_api_path(self):
        return "/api/v3/kwaivgi/kling-video-o3-pro/text-to-video"
