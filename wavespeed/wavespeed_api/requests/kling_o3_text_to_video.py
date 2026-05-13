# ABOUTME: Kling O3 text-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the kling-video-o3-std text-to-video endpoint under /kwaivgi/.

from typing import List, Optional
from pydantic import Field
from ..utils import BaseRequest


class KlingO3TextToVideo(BaseRequest):
    """
    Kling O3 text-to-video model.

    Generates a short video from a text prompt. Exposes the full documented
    parameter set: sound, shot type, and multi-prompt scene segmentation.
    """

    prompt: Optional[str] = Field(
        default=None,
        description="Positive prompt describing the desired video. Mutually exclusive with multi_prompt; one must be provided.",
    )
    duration: Optional[int] = Field(
        default=5,
        description="Video duration in seconds (3-15).",
        ge=3,
        le=15,
    )
    aspect_ratio: Optional[str] = Field(
        default="16:9",
        description="Aspect ratio of the output video (e.g. '16:9', '9:16', '1:1').",
    )
    sound: Optional[bool] = Field(
        default=False,
        description="Enable synchronized audio generation.",
    )
    shot_type: Optional[str] = Field(
        default="intelligent",
        description="Shot composition mode: 'intelligent' or 'customize'.",
    )
    multi_prompt: Optional[List[dict]] = Field(
        default=None,
        description="Scene-segmented prompt list; mutually exclusive with prompt.",
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "duration": self.duration,
            "aspect_ratio": self.aspect_ratio,
            "sound": self.sound,
            "shot_type": self.shot_type,
            "multi_prompt": self.multi_prompt,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/kwaivgi/kling-video-o3-std/text-to-video"

    def field_required(self):
        return []

    def field_order(self):
        return [
            "prompt",
            "duration",
            "aspect_ratio",
            "sound",
            "shot_type",
            "multi_prompt",
        ]
