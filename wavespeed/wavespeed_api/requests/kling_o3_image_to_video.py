# ABOUTME: Kling O3 image-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the kling-video-o3-std image-to-video endpoint under /kwaivgi/.

from typing import List, Optional
from pydantic import Field
from ..utils import BaseRequest


class KlingO3ImageToVideo(BaseRequest):
    """
    Kling O3 image-to-video model.

    Generates a short video from a starting image and a text prompt.
    Supports end-frame guidance, optional audio, shot composition mode,
    and multi-prompt scene segmentation.
    """

    prompt: str = Field(..., description="The positive prompt describing the desired motion, camera, and action.")
    image: str = Field(..., description="URL of the starting image.")
    end_image: Optional[str] = Field(
        default=None,
        description="URL of an optional end-frame guidance image.",
    )
    duration: Optional[int] = Field(
        default=5,
        description="Video duration in seconds (3-15).",
        ge=3,
        le=15,
    )
    sound: Optional[bool] = Field(
        default=None,
        description="Enable synchronized audio generation (adds roughly 33% to base cost).",
    )
    shot_type: Optional[str] = Field(
        default=None,
        description="Shot composition mode: 'intelligent' (auto) or 'customize' (manual).",
    )
    multi_prompt: Optional[List[dict]] = Field(
        default=None,
        description="Scene-segmented prompt list for multi-shot compositions.",
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "image": self.image,
            "end_image": self.end_image,
            "duration": self.duration,
            "sound": self.sound,
            "shot_type": self.shot_type,
            "multi_prompt": self.multi_prompt,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/kwaivgi/kling-video-o3-std/image-to-video"

    def field_required(self):
        return ["prompt", "image"]

    def field_order(self):
        return [
            "prompt",
            "image",
            "end_image",
            "duration",
            "sound",
            "shot_type",
            "multi_prompt",
        ]
