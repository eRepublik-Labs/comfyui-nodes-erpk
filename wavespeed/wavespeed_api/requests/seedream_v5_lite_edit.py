# ABOUTME: ByteDance Seedream V5.0 Lite Edit request model for WaveSpeed AI.
# ABOUTME: Inherits from Seedream V4.5 Edit for image editing capabilities.

from .seedream_v4_5_edit import SeedreamV4_5Edit


class SeedreamV5LiteEdit(SeedreamV4_5Edit):
    """
    ByteDance Seedream V5.0 Lite Edit image editing model
    """

    def get_api_path(self):
        """Gets the API path."""
        return "/api/v3/bytedance/seedream-v5.0-lite/edit"
