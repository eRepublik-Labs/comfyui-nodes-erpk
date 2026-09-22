# ABOUTME: ByteDance Seedream V5.0 Pro edit request model for WaveSpeed AI.
# ABOUTME: Edits from up to 10 reference images; an unset aspect ratio follows the first image.

from typing import List, Optional
from pydantic import Field
from .seedream_v5_pro import SeedreamV5Pro


class SeedreamV5ProEdit(SeedreamV5Pro):
    """
    ByteDance Seedream V5.0 Pro edit model.

    Takes the text-to-image settings plus 1 to 10 reference images. Leaving
    `aspect_ratio` unset lets the API pick the supported ratio closest to the
    first image.
    """

    images: List[str] = Field(..., description="Image URLs or data URIs to edit (1-10).",
                              min_length=1, max_length=10)
    aspect_ratio: Optional[str] = Field(default=None, description="Aspect ratio; unset follows the first image.")

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = super().build_payload()
        payload["images"] = self.images
        return payload

    def get_api_path(self):
        """Gets the API path."""
        return "/api/v3/bytedance/seedream-v5.0-pro/edit"

    def field_required(self):
        return ["prompt", "images"]

    def field_order(self):
        return ["prompt", "images"] + super().field_order()[1:]
