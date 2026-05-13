# ABOUTME: Kling 2.6 Std image-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the kling-v2.6-std image-to-video endpoint under /kwaivgi/.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class KlingV2_6StdImageToVideo(BaseRequest):
    """
    Kling 2.6 Std image-to-video model.

    Generates a short video from a starting image and a text prompt.
    """

    prompt: str = Field(..., description="The positive prompt describing the desired motion.")
    image: str = Field(..., description="URL of the starting image (JPG/JPEG/PNG, max 10MB, min 300px each side).")
    negative_prompt: Optional[str] = Field(
        default=None,
        description="Elements to exclude from the generated video.",
    )
    duration: Optional[int] = Field(
        default=5,
        description="Video duration in seconds (5 or 10).",
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "image": self.image,
            "negative_prompt": self.negative_prompt,
            "duration": self.duration,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/kwaivgi/kling-v2.6-std/image-to-video"

    def field_required(self):
        return ["prompt", "image"]

    def field_order(self):
        return [
            "prompt",
            "image",
            "negative_prompt",
            "duration",
        ]
