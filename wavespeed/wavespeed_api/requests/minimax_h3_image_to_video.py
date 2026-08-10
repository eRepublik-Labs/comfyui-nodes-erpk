# ABOUTME: MiniMax H3 image-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the wavespeed-ai/minimax-h3 image-to-video endpoint.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class MinimaxH3ImageToVideo(BaseRequest):
    """
    MiniMax H3 image-to-video model.

    Animates a first-frame image, optionally interpolating toward a last frame.
    The output canvas follows the first image's aspect ratio, so there is no
    aspect ratio parameter. Audio is steered by an `Audio:` line in the prompt.
    """

    prompt: str = Field(..., description="Motion, camera movement, and an `Audio:` line for the soundtrack.")
    image: str = Field(..., description="First-frame image URL or data URI.")
    last_image: Optional[str] = Field(
        default=None,
        description="Last-frame image URL for interpolation between frames.",
    )
    resolution: Optional[str] = Field(
        default="480p",
        description="Video resolution: 480p or 768p.",
    )
    duration: Optional[int] = Field(
        default=5,
        description="Video duration in seconds.",
        ge=3,
        le=15,
    )
    seed: Optional[int] = Field(
        default=-1,
        description="Random seed; -1 generates a random seed.",
        ge=-1,
        le=2147483647,
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "image": self.image,
            "last_image": self.last_image,
            "resolution": self.resolution,
            "duration": self.duration,
            "seed": self.seed,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path. Corresponds to api_path in the JSON."""
        return "/api/v3/wavespeed-ai/minimax-h3/image-to-video"

    def field_required(self):
        return ["prompt", "image"]

    def field_order(self):
        return ["prompt", "image", "last_image", "resolution", "duration", "seed"]
