# ABOUTME: MiniMax H3 text-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the wavespeed-ai/minimax-h3 text-to-video endpoint.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class MinimaxH3TextToVideo(BaseRequest):
    """
    MiniMax H3 text-to-video model.

    Produces picture and native stereo audio in a single pass at 24fps. Audio is
    steered by an `Audio:` line inside the prompt rather than a parameter.
    Duration snaps to the model's frame grid, so a 5s request lands near 5.2s.
    """

    prompt: str = Field(..., description="Scene, action, camera movement, and an `Audio:` line for the soundtrack.")
    aspect_ratio: Optional[str] = Field(
        default="16:9",
        description="Video aspect ratio: 16:9, 9:16, 1:1, 4:3, 3:4, 21:9, or 9:21.",
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
            "aspect_ratio": self.aspect_ratio,
            "resolution": self.resolution,
            "duration": self.duration,
            "seed": self.seed,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path. Corresponds to api_path in the JSON."""
        return "/api/v3/wavespeed-ai/minimax-h3/text-to-video"

    def field_required(self):
        return ["prompt"]

    def field_order(self):
        return ["prompt", "aspect_ratio", "resolution", "duration", "seed"]
