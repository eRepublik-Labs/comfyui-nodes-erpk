# ABOUTME: LTX 2.3 text-to-video request via WaveSpeed.
# ABOUTME: Routes to the /api/v3/wavespeed-ai/ltx-2.3/text-to-video endpoint.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class Ltx23TextToVideo(BaseRequest):
    """
    WaveSpeed LTX 2.3 text-to-video model.
    Generates video with configurable resolution, aspect ratio, and duration.
    """

    prompt: str = Field(..., description="Positive prompt for generation.")
    resolution: Optional[str] = Field(
        default="720p",
        description="Output resolution: 480p, 720p, or 1080p.",
    )
    aspect_ratio: Optional[str] = Field(
        default="16:9",
        description="Output aspect ratio: 16:9 or 9:16.",
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
            "prompt": self.prompt,
            "resolution": self.resolution,
            "aspect_ratio": self.aspect_ratio,
            "duration": self.duration,
            "seed": self.seed,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/wavespeed-ai/ltx-2.3/text-to-video"

    def field_required(self):
        return ["prompt"]

    def field_order(self):
        return ["prompt", "resolution", "aspect_ratio", "duration", "seed"]
