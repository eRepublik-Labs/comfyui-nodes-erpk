# ABOUTME: ByteDance Seedream V5.0 Lite Sequential request model for WaveSpeed AI.
# ABOUTME: Inherits from Seedream V4.5 Sequential for multi-image generation.

from .seedream_v4_5_sequential import SeedreamV4_5Sequential


class SeedreamV5LiteSequential(SeedreamV4_5Sequential):
    """
    ByteDance Seedream V5.0 Lite Sequential text to image model
    """

    def get_api_path(self):
        """Gets the API path."""
        return "/api/v3/bytedance/seedream-v5.0-lite/sequential"
