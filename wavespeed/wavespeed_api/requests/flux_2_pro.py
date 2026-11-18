# ABOUTME: FLUX.2 Pro text-to-image request model for WaveSpeed AI.
# ABOUTME: Sized by a "width*height" string, with a seed sent to the API.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class Flux2Pro(BaseRequest):
    """FLUX.2 Pro text-to-image model."""

    prompt: str = Field(..., description="The positive prompt for the generation.")
    size: Optional[str] = Field(default="1024*1024", description="Output size as width*height.")
    seed: Optional[int] = Field(default=-1, description="Random seed; -1 picks a random seed.")

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "size": self.size,
            "seed": self.seed,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path."""
        return "/api/v3/wavespeed-ai/flux-2-pro/text-to-image"

    def field_required(self):
        return ["prompt"]

    def field_order(self):
        return ["prompt", "size", "seed"]
