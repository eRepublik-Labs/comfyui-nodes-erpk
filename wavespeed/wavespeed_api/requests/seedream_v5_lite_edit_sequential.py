# ABOUTME: ByteDance Seedream V5.0 Lite Edit Sequential request model for WaveSpeed AI.
# ABOUTME: Inherits from Seedream V4.5 Edit Sequential for multi-image editing.

from .seedream_v4_5_edit_sequential import SeedreamV4_5EditSequential


class SeedreamV5LiteEditSequential(SeedreamV4_5EditSequential):
    """
    ByteDance Seedream V5.0 Lite Edit Sequential image editing model
    """

    def get_api_path(self):
        """Gets the API path."""
        return "/api/v3/bytedance/seedream-v5.0-lite/edit-sequential"
