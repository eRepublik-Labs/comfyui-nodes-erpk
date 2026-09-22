# ABOUTME: ByteDance Seedream V5.0 Pro text-to-image request model for WaveSpeed AI.
# ABOUTME: Sized by aspect ratio plus a 1k/1.5k/2k resolution tier, not by width and height.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest

ASPECT_RATIOS = ["1:1", "1:2", "2:1", "1:3", "3:1", "2:3", "3:2", "3:4", "4:3",
                 "4:5", "5:4", "9:16", "16:9", "9:21", "21:9"]
RESOLUTIONS = ["1k", "1.5k", "2k"]
OUTPUT_FORMATS = ["jpeg", "png"]
PROMPT_OPTIMIZATION_MODES = ["standard", "fast"]


class SeedreamV5Pro(BaseRequest):
    """
    ByteDance Seedream V5.0 Pro text-to-image model.

    The endpoint takes no seed and no pixel size: the output is shaped by
    `aspect_ratio` and priced by the `resolution` tier.
    """

    prompt: str = Field(..., description="The positive prompt for the generation.")
    aspect_ratio: Optional[str] = Field(default="1:1", description="Aspect ratio of the generated image.")
    resolution: Optional[str] = Field(default="1k", description="Output resolution tier: 1k, 1.5k or 2k.")
    output_format: Optional[str] = Field(default="jpeg", description="Output image format: jpeg or png.")
    prompt_optimization_mode: Optional[str] = Field(
        default="standard", description="Prompt rewrite before generation: standard or fast.")
    enable_sync_mode: Optional[bool] = Field(default=False, description="Wait for the result inline.")
    enable_base64_output: Optional[bool] = Field(default=False, description="Return base64 instead of a URL.")

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "aspect_ratio": self.aspect_ratio,
            "resolution": self.resolution,
            "output_format": self.output_format,
            "prompt_optimization_mode": self.prompt_optimization_mode,
            "enable_sync_mode": self.enable_sync_mode,
            "enable_base64_output": self.enable_base64_output,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path."""
        return "/api/v3/bytedance/seedream-v5.0-pro"

    def field_required(self):
        return ["prompt"]

    def field_order(self):
        return ["prompt", "aspect_ratio", "resolution", "output_format", "prompt_optimization_mode",
                "enable_sync_mode", "enable_base64_output"]
