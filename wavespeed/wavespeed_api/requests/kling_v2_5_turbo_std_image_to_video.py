# ABOUTME: Kling 2.5 Turbo Std image-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the kling-v2.5-turbo-std image-to-video endpoint under /kwaivgi/.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class KlingV2_5TurboStdImageToVideo(BaseRequest):
    """
    Kling 2.5 Turbo Std image-to-video model.

    Generates a short video from a starting image and a text prompt using the
    standard Kling 2.5 Turbo endpoint.
    """

    prompt: str = Field(..., description="The positive prompt describing the desired motion.")
    image: str = Field(..., description="URL of the starting image.")
    negative_prompt: Optional[str] = Field(
        default="",
        description="Elements to suppress or avoid in the generated video.",
    )
    guidance_scale: Optional[float] = Field(
        default=0.5,
        description="Prompt adherence; higher values reduce creative deviation (0.0-1.0).",
        ge=0.0,
        le=1.0,
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
            "guidance_scale": self.guidance_scale,
            "duration": self.duration,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/kwaivgi/kling-v2.5-turbo-std/image-to-video"

    def field_required(self):
        return ["prompt", "image"]

    def field_order(self):
        return [
            "prompt",
            "image",
            "negative_prompt",
            "guidance_scale",
            "duration",
        ]
