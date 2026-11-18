# ABOUTME: ByteDance Seedream V5.5 layer-decomposition request model for WaveSpeed AI.
# ABOUTME: Splits one image into a clean base plus transparent PNG layers, billed per requested image.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class SeedreamV5_5Layers(BaseRequest):
    """
    ByteDance Seedream V5.5 layer decomposition.

    Always requests PNG, because the layers' transparency is what separates
    each object. `max_images` counts the base plus the layers and sets the
    price, even when fewer images come back.
    """

    image: str = Field(..., description="Image URL or data URI to decompose.")
    prompt: Optional[str] = Field(default=None, description="Optional guidance for the decomposition.")
    resolution: Optional[str] = Field(default="1k", description="Output resolution tier: 1k, 1.5k or 2k.")
    max_images: int = Field(default=10, ge=2, le=100, description="Most images to return, base included (2-100).")

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "image": self.image,
            "prompt": self.prompt,
            "resolution": self.resolution,
            "max_images": self.max_images,
            "output_format": "png",
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path."""
        return "/api/v3/bytedance/seedream-v5.5/layer-decomposition"

    def field_required(self):
        return ["image"]

    def field_order(self):
        return ["image", "prompt", "resolution", "max_images", "output_format"]
