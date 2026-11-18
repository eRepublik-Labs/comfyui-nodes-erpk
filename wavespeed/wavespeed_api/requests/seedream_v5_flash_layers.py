# ABOUTME: ByteDance Seedream V5.0 Flash layer-decomposition request model for WaveSpeed AI.
# ABOUTME: Splits one image into a clean base plus up to 16 transparent PNG layers.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class SeedreamV5FlashLayers(BaseRequest):
    """
    ByteDance Seedream V5.0 Flash layer decomposition.

    Always requests PNG, because the layers' transparency is what separates
    each object.
    """

    image: str = Field(..., description="Image URL or data URI to decompose.")
    prompt: Optional[str] = Field(default=None, description="Optional guidance for the decomposition.")
    resolution: Optional[str] = Field(default="1k", description="Output resolution tier: 1k, 1.5k or 2k.")

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "image": self.image,
            "prompt": self.prompt,
            "resolution": self.resolution,
            "output_format": "png",
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path."""
        return "/api/v3/bytedance/seedream-v5.0-flash/layer-decomposition"

    def field_required(self):
        return ["image"]

    def field_order(self):
        return ["image", "prompt", "resolution", "output_format"]
