# ABOUTME: Qwen Image Multiple Angles request on WaveSpeed's 96-pose camera system.
# ABOUTME: Re-renders a subject from one of 8 azimuths, 4 elevations and 3 framing distances.

from typing import List, Literal, Optional
from pydantic import Field
from ..utils import BaseRequest


class QwenImageMultipleAngles96(BaseRequest):
    """
    Qwen Image edit-multiple-angles model.

    The server snaps any angle to its nearest pose, so the fields accept only
    the poses it renders: 8 azimuths x 4 elevations x 3 distances = 96.
    """

    images: List[str] = Field(..., min_length=1, max_length=3,
                              description="Reference image URLs or data URIs (1-3).")
    horizontal_angle: Literal[0, 45, 90, 135, 180, 225, 270, 315] = Field(
        default=0, description="Camera azimuth in degrees: 0 front, 90 right side, 180 back, 270 left side.")
    vertical_angle: Literal[-30, 0, 30, 60] = Field(
        default=0, description="Camera elevation in degrees: -30 low, 0 eye level, 30 elevated, 60 high.")
    distance: Literal[0, 1, 2] = Field(default=1, description="Framing: 0 close-up, 1 medium, 2 wide.")
    prompt: Optional[str] = Field(default=None, description="Extra guidance appended to the angle prompt.")
    seed: int = Field(default=-1, ge=-1, le=2147483647,
                      description="Random seed; -1 generates a random seed.")
    output_format: Literal["jpeg", "png", "webp"] = Field(default="jpeg", description="Output image format.")

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "images": self.images,
            "horizontal_angle": self.horizontal_angle,
            "vertical_angle": self.vertical_angle,
            "distance": self.distance,
            "prompt": self.prompt,
            "seed": self.seed,
            "output_format": self.output_format,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self) -> str:
        """Gets the API path."""
        return "/api/v3/wavespeed-ai/qwen-image/edit-multiple-angles"

    def field_required(self):
        return ["images"]

    def field_order(self):
        return ["images", "horizontal_angle", "vertical_angle", "distance", "prompt", "seed", "output_format"]
