# ABOUTME: LTX 2.3 image-to-video request via WaveSpeed.
# ABOUTME: Routes to the /api/v3/wavespeed-ai/ltx-2.3/image-to-video endpoint.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class Ltx23ImageToVideo(BaseRequest):
    """
    WaveSpeed LTX 2.3 image-to-video model.
    Animates a source image with configurable resolution and duration.
    Aspect ratio is inferred from the source image.
    """

    image: str = Field(..., description="Source image URL.")
    prompt: str = Field(..., description="Positive prompt for generation.")
    resolution: Optional[str] = Field(
        default="720p",
        description="Output resolution: 480p, 720p, or 1080p.",
    )
    duration: Optional[int] = Field(
        default=5,
        ge=5,
        le=20,
        description="Duration in seconds (5-20).",
    )
    seed: Optional[int] = Field(
        default=-1,
        ge=-1,
        le=2147483647,
        description="Random seed; -1 uses a random seed.",
    )

    def build_payload(self) -> dict:
        payload = {
            "image": self.image,
            "prompt": self.prompt,
            "resolution": self.resolution,
            "duration": self.duration,
            "seed": self.seed,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/wavespeed-ai/ltx-2.3/image-to-video"

    def field_required(self):
        return ["image", "prompt"]

    def field_order(self):
        return ["image", "prompt", "resolution", "duration", "seed"]
