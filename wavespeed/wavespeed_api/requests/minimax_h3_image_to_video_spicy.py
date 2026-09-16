# ABOUTME: MiniMax H3 Spicy image-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the wavespeed-ai/minimax-h3 image-to-video-spicy endpoint.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class MinimaxH3ImageToVideoSpicy(BaseRequest):
    """
    MiniMax H3 Spicy image-to-video model.

    Same inputs as image-to-video except that the prompt is optional: the
    model can animate a start frame with no text guidance. There is no LoRA
    twin for this tier.
    """

    image: str = Field(..., description="Start-frame image URL or data URI.")
    prompt: Optional[str] = Field(default=None, description="Scene, action, camera movement and mood.")
    last_image: Optional[str] = Field(
        default=None,
        description="Optional end-frame image URL.",
    )
    resolution: Optional[str] = Field(
        default="480p",
        description="Video resolution: 480p, 540p, 768p or 1080p.",
    )
    duration: Optional[int] = Field(
        default=5,
        description="Video duration in seconds.",
        ge=3,
        le=15,
    )
    seed: Optional[int] = Field(
        default=-1,
        description="Random seed; a negative value generates a random seed.",
        ge=-1,
        le=2147483647,
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "image": self.image,
            "prompt": self.prompt,
            "last_image": self.last_image,
            "resolution": self.resolution,
            "duration": self.duration,
            "seed": self.seed,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path. Corresponds to api_path in the JSON."""
        return "/api/v3/wavespeed-ai/minimax-h3/image-to-video-spicy"

    def field_required(self):
        return ["image"]

    def field_order(self):
        return ["image", "prompt", "last_image", "resolution", "duration", "seed"]
