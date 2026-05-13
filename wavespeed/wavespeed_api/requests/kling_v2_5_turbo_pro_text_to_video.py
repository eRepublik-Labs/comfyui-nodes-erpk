# ABOUTME: Kling 2.5 Turbo Pro text-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the kling-v2.5-turbo-pro text-to-video endpoint under /kwaivgi/.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class KlingV2_5TurboProTextToVideo(BaseRequest):
    """
    Kling 2.5 Turbo Pro text-to-video model.

    Generates a short video from a text prompt. Only a Pro tier is offered by
    WaveSpeed for this modality.
    """

    prompt: str = Field(..., description="The positive prompt describing the desired scene and motion.")
    negative_prompt: Optional[str] = Field(
        default="",
        description="Elements to suppress or avoid in the generated video.",
    )
    aspect_ratio: Optional[str] = Field(
        default="16:9",
        description="Aspect ratio of the output video ('16:9', '9:16', or '1:1').",
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
        payload = {
            "prompt": self.prompt,
            "negative_prompt": self.negative_prompt,
            "aspect_ratio": self.aspect_ratio,
            "guidance_scale": self.guidance_scale,
            "duration": self.duration,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/kwaivgi/kling-v2.5-turbo-pro/text-to-video"

    def field_required(self):
        return ["prompt"]

    def field_order(self):
        return [
            "prompt",
            "negative_prompt",
            "aspect_ratio",
            "guidance_scale",
            "duration",
        ]
