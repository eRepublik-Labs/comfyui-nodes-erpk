# ABOUTME: ByteDance Seedream V5.0 Flash text-to-image request model for WaveSpeed AI.
# ABOUTME: Sized by aspect ratio plus a resolution tier, at one flat price per image.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class SeedreamV5Flash(BaseRequest):
    """
    ByteDance Seedream V5.0 Flash text-to-image model.

    The endpoint takes no seed and no pixel size: the output is shaped by
    `aspect_ratio` and `resolution`.
    """

    prompt: str = Field(..., description="The positive prompt for the generation.")
    aspect_ratio: Optional[str] = Field(default="1:1", description="Aspect ratio of the generated image.")
    resolution: Optional[str] = Field(default="1k", description="Output resolution tier: 1k, 1.5k or 2k.")
    output_format: Optional[str] = Field(default="jpeg", description="Output image format: jpeg or png.")

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "aspect_ratio": self.aspect_ratio,
            "resolution": self.resolution,
            "output_format": self.output_format,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path."""
        return "/api/v3/bytedance/seedream-v5.0-flash"

    def field_required(self):
        return ["prompt"]

    def field_order(self):
        return ["prompt", "aspect_ratio", "resolution", "output_format"]
