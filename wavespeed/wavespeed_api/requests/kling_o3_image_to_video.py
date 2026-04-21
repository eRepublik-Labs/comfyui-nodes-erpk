# ABOUTME: Kling O3 image-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the kling-video-o3-std image-to-video endpoint under /kwaivgi/.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class KlingO3ImageToVideo(BaseRequest):
    """
    Kling O3 image-to-video model.

    Generates a short video from a starting image and a text prompt.
    """

    prompt: str = Field(..., description="The positive prompt describing the desired motion.")
    image: str = Field(..., description="URL of the starting image.")
    duration: Optional[int] = Field(
        default=5,
        description="Video duration in seconds (3-10).",
        ge=3,
        le=10,
    )
    aspect_ratio: Optional[str] = Field(
        default="16:9",
        description="Aspect ratio of the output video (e.g. '16:9', '9:16', '1:1').",
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
            "seed": self.seed,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/kwaivgi/kling-video-o3-std/image-to-video"

    def field_required(self):
        return ["prompt", "image"]

    def field_order(self):
        return [
            "prompt",
            "image",
            "duration",
            "aspect_ratio",
            "seed",
        ]
