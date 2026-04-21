# ABOUTME: Seedance 2.0 image-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the bytedance/seedance-2.0 image-to-video endpoint.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class Seedance20ImageToVideo(BaseRequest):
    """
    Seedance 2.0 image-to-video model.

    Animates a source image into a short video clip driven by a text prompt.
    """

    prompt: str = Field(..., description="Text description of the desired motion.")
    image: str = Field(..., description="URL of the source image to animate.")
    duration: Optional[int] = Field(
        default=5,
        description="Video duration in seconds.",
        ge=3,
        le=12,
    )
    aspect_ratio: Optional[str] = Field(
        default="16:9",
        description="Video aspect ratio: 16:9, 9:16, or 1:1.",
    )
    resolution: Optional[str] = Field(
        default="720p",
        description="Video resolution: 480p, 720p, or 1080p.",
    )
    seed: Optional[int] = Field(
        default=-1,
        description="Random seed; -1 generates random seed.",
        ge=-1,
        le=2147483647,
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "image": self.image,
            "duration": self.duration,
            "aspect_ratio": self.aspect_ratio,
            "resolution": self.resolution,
            "seed": self.seed,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path. Corresponds to api_path in the JSON."""
        return "/api/v3/bytedance/seedance-2.0/image-to-video"

    def field_required(self):
        return ["prompt", "image"]

    def field_order(self):
        return [
            "prompt",
            "image",
            "duration",
            "aspect_ratio",
            "resolution",
            "seed",
        ]
