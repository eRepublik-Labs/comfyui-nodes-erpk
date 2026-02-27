# ABOUTME: ByteDance Seedream V5.0 Lite text-to-image request model for WaveSpeed AI.
# ABOUTME: Inherits from Seedream V4.5 with higher minimum resolution (1440px).

from typing import Optional
from pydantic import Field
from .seedream_v4_5 import SeedreamV4_5


class SeedreamV5Lite(SeedreamV4_5):
    """
    ByteDance Seedream V5.0 Lite text to image model
    """

    width: Optional[int] = Field(
        default=2048, description="The width of the generated image.", ge=1440, le=4096
    )
    height: Optional[int] = Field(
        default=2048, description="The height of the generated image.", ge=1440, le=4096
    )

    def get_api_path(self):
        """Gets the API path. Corresponds to api_path in the JSON."""
        return "/api/v3/bytedance/seedream-v5.0-lite"
