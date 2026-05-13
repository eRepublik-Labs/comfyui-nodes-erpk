# ABOUTME: Kling 3.0 4K text-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the kling-v3.0-4k text-to-video endpoint with identical payload to Std/Pro.

from .kling_v3_text_to_video import KlingV3TextToVideo


class KlingV34KTextToVideo(KlingV3TextToVideo):
    """Kling 3.0 4K text-to-video — same parameters, different endpoint."""

    def get_api_path(self):
        return "/api/v3/kwaivgi/kling-v3.0-4k/text-to-video"
