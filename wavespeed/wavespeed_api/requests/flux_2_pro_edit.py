# ABOUTME: FLUX.2 Pro edit request model for WaveSpeed AI.
# ABOUTME: Edits from up to 3 reference images; an unset size lets the API choose.

from typing import List, Optional
from pydantic import Field
from .flux_2_pro import Flux2Pro


class Flux2ProEdit(Flux2Pro):
    """FLUX.2 Pro edit model: the text-to-image settings plus 1 to 3 reference images."""

    images: List[str] = Field(..., description="Image URLs or data URIs to edit (1-3).",
                              min_length=1, max_length=3)
    size: Optional[str] = Field(default=None, description="Output size as width*height; unset lets the API choose.")

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = super().build_payload()
        payload["images"] = self.images
        return payload

    def get_api_path(self):
        """Gets the API path."""
        return "/api/v3/wavespeed-ai/flux-2-pro/edit"

    def field_required(self):
        return ["prompt", "images"]

    def field_order(self):
        return ["prompt", "images", "size", "seed"]
