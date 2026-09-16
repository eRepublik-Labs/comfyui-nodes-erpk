# ABOUTME: MiniMax H3 image-to-video request for WaveSpeed AI.
# ABOUTME: Routes to MiniMax's own minimax/h3 image-to-video endpoint.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class MinimaxH3ImageToVideo(BaseRequest):
    """
    MiniMax H3 image-to-video model, MiniMax-hosted edition.

    Animates a first-frame image, optionally interpolating toward a last frame.
    The output canvas follows the first image's aspect ratio, so there is no
    aspect ratio parameter. The endpoint documents no seed.
    """

    prompt: str = Field(..., description="Motion, camera movement, and an `Audio:` line for the soundtrack.")
    image: str = Field(..., description="First-frame image URL or data URI (256-5760 px per side).")
    last_image: Optional[str] = Field(
        default=None,
        description="Last-frame image URL for interpolation between frames.",
    )
    resolution: Optional[str] = Field(
        default="768p",
        description="Video resolution: 768p or 2k.",
    )
    duration: Optional[int] = Field(
        default=5,
        description="Video duration in seconds.",
        ge=4,
        le=15,
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "image": self.image,
            "last_image": self.last_image,
            "resolution": self.resolution,
            "duration": self.duration,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path. Corresponds to api_path in the JSON."""
        return "/api/v3/minimax/h3/image-to-video"

    def field_required(self):
        return ["prompt", "image"]

    def field_order(self):
        return ["prompt", "image", "last_image", "resolution", "duration"]
