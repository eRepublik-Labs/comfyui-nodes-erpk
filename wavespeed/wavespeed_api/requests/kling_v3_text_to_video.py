# ABOUTME: Kling 3.0 text-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the kling-v3.0-std text-to-video endpoint under /kwaivgi/.

from typing import List, Optional
from pydantic import Field
from ..utils import BaseRequest


class KlingV3TextToVideo(BaseRequest):
    """
    Kling 3.0 text-to-video model.

    Generates a short video from a text prompt. Exposes the full documented
    parameter set: negative prompt, cfg_scale, sound, shot type, multi-prompt
    scene segmentation, and element list for visual consistency.
    """

    prompt: Optional[str] = Field(
        default=None,
        description="Positive prompt describing the desired video. Mutually exclusive with multi_prompt; one must be provided.",
    )
    negative_prompt: Optional[str] = Field(
        default=None,
        description="Elements to exclude from the generation.",
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
    cfg_scale: Optional[float] = Field(
        default=0.5,
        description="Prompt adherence strength (0-1). Higher means stricter adherence.",
        ge=0.0,
        le=1.0,
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
    element_list: Optional[List[dict]] = Field(
        default=None,
        description="Pre-generated element IDs for visual consistency across scenes.",
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "negative_prompt": self.negative_prompt,
            "duration": self.duration,
            "aspect_ratio": self.aspect_ratio,
            "cfg_scale": self.cfg_scale,
            "sound": self.sound,
            "shot_type": self.shot_type,
            "multi_prompt": self.multi_prompt,
            "element_list": self.element_list,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/kwaivgi/kling-v3.0-std/text-to-video"

    def field_required(self):
        return []

    def field_order(self):
        return [
            "prompt",
            "negative_prompt",
            "duration",
            "aspect_ratio",
            "cfg_scale",
            "sound",
            "shot_type",
            "multi_prompt",
            "element_list",
        ]
