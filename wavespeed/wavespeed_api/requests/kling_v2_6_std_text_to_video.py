# ABOUTME: Kling 2.6 Std text-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the kling-v2.6-std text-to-video endpoint under /kwaivgi/.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class KlingV2_6StdTextToVideo(BaseRequest):
    """
    Kling 2.6 Std text-to-video model.

    Generates a short video from a text prompt.
    """

    prompt: str = Field(..., description="The positive prompt describing the desired video.")
    negative_prompt: Optional[str] = Field(
        default=None,
        description="Elements to exclude from the generated video.",
    )
    aspect_ratio: Optional[str] = Field(
        default="16:9",
        description="Aspect ratio of the output video (1:1, 9:16, or 16:9).",
    )
    duration: Optional[int] = Field(
        default=5,
        description="Video duration in seconds (5 or 10).",
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "negative_prompt": self.negative_prompt,
            "aspect_ratio": self.aspect_ratio,
            "duration": self.duration,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/kwaivgi/kling-v2.6-std/text-to-video"

    def field_required(self):
        return ["prompt"]

    def field_order(self):
        return [
            "prompt",
            "negative_prompt",
            "aspect_ratio",
            "duration",
        ]
