# ABOUTME: MiniMax H3 text-to-video request for WaveSpeed AI.
# ABOUTME: Routes to MiniMax's own minimax/h3 text-to-video endpoint.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class MinimaxH3TextToVideo(BaseRequest):
    """
    MiniMax H3 text-to-video model, MiniMax-hosted edition.

    Produces picture and native stereo audio in a single pass. Audio is steered
    by an `Audio:` line inside the prompt rather than a parameter. The endpoint
    documents no seed.
    """

    prompt: str = Field(..., description="Scene, action, camera movement, and an `Audio:` line for the soundtrack.")
    aspect_ratio: Optional[str] = Field(
        default="16:9",
        description="Video aspect ratio: 21:9, 16:9, 4:3, 1:1, 3:4, or 9:16.",
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
            "aspect_ratio": self.aspect_ratio,
            "resolution": self.resolution,
            "duration": self.duration,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path. Corresponds to api_path in the JSON."""
        return "/api/v3/minimax/h3/text-to-video"

    def field_required(self):
        return ["prompt"]

    def field_order(self):
        return ["prompt", "aspect_ratio", "resolution", "duration"]
