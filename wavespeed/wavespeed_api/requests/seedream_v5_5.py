# ABOUTME: ByteDance Seedream V5.5 text-to-image request model for WaveSpeed AI.
# ABOUTME: Sized by aspect ratio plus a resolution tier, with an auto, transparent or opaque background.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest

BACKGROUNDS = ["auto", "transparent", "opaque"]


class SeedreamV5_5(BaseRequest):
    """
    ByteDance Seedream V5.5 text-to-image model.

    The endpoint takes no seed and no pixel size: the output is shaped by
    `aspect_ratio` and priced by the `resolution` tier.
    """

    prompt: str = Field(..., description="The positive prompt for the generation.")
    aspect_ratio: Optional[str] = Field(default="1:1", description="Aspect ratio of the generated image.")
    resolution: Optional[str] = Field(default="1k", description="Output resolution tier: 1k, 1.5k or 2k.")
    output_format: Optional[str] = Field(default="png", description="Output image format: jpeg or png.")
    background: Optional[str] = Field(default="auto", description="Background: auto, transparent or opaque.")

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "aspect_ratio": self.aspect_ratio,
            "resolution": self.resolution,
            "output_format": self.output_format,
            "background": self.background,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path."""
        return "/api/v3/bytedance/seedream-v5.5"

    def field_required(self):
        return ["prompt"]

    def field_order(self):
        return ["prompt", "aspect_ratio", "resolution", "output_format", "background"]
