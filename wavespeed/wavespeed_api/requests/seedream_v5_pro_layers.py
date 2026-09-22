# ABOUTME: ByteDance Seedream V5.0 Pro layer-decomposition request model for WaveSpeed AI.
# ABOUTME: Splits one image into a clean base plus one transparent PNG per object.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class SeedreamV5ProLayers(BaseRequest):
    """
    ByteDance Seedream V5.0 Pro layer decomposition.

    Always requests PNG: with jpeg the API returns jpeg layers and the
    transparency that separates each object is lost.
    """

    image: str = Field(..., description="Image URL or data URI to decompose.")
    prompt: Optional[str] = Field(default=None, description="Optional guidance for the decomposition.")
    resolution: Optional[str] = Field(default="1k", description="Output resolution tier: 1k, 1.5k or 2k.")
    prompt_optimization_mode: Optional[str] = Field(
        default="standard", description="Prompt rewrite before generation: standard or fast.")

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "image": self.image,
            "prompt": self.prompt,
            "resolution": self.resolution,
            "output_format": "png",
            "prompt_optimization_mode": self.prompt_optimization_mode,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path."""
        return "/api/v3/bytedance/seedream-v5.0-pro/layer-decomposition"

    def field_required(self):
        return ["image"]

    def field_order(self):
        return ["image", "prompt", "resolution", "output_format", "prompt_optimization_mode"]
