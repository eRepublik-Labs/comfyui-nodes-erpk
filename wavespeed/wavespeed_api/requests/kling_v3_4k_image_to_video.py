# ABOUTME: Kling 3.0 4K image-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the kling-v3.0-4k image-to-video endpoint with the documented 4K parameter set.

from typing import List, Optional
from pydantic import Field
from ..utils import BaseRequest


class KlingV34KImageToVideo(BaseRequest):
    """
    Kling 3.0 4K image-to-video model.

    Generates a high-resolution short video from a starting image.
    The 4K endpoint derives aspect ratio from the input image and exposes
    additional controls (negative prompt, end frame, cfg_scale, sound, shot type,
    multi-prompt scene segmentation, and element list) compared to Std/Pro.
    """

    prompt: Optional[str] = Field(
        default=None,
        description="Positive prompt describing the desired motion. Mutually exclusive with multi_prompt; one must be provided.",
    )
    image: str = Field(..., description="URL of the starting image (JPG/PNG, <=10MB, min 300px per side, aspect 1:2.5 to 2.5:1).")
    negative_prompt: Optional[str] = Field(
        default=None,
        description="Elements to exclude from the generation.",
    )
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
        default="customize",
        description="Shot composition mode: 'customize' or 'intelligent'.",
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
            "image": self.image,
            "negative_prompt": self.negative_prompt,
            "end_image": self.end_image,
            "duration": self.duration,
            "cfg_scale": self.cfg_scale,
            "sound": self.sound,
            "shot_type": self.shot_type,
            "multi_prompt": self.multi_prompt,
            "element_list": self.element_list,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/kwaivgi/kling-v3.0-4k/image-to-video"

    def field_required(self):
        return ["image"]

    def field_order(self):
        return [
            "prompt",
            "image",
            "negative_prompt",
            "end_image",
            "duration",
            "cfg_scale",
            "sound",
            "shot_type",
            "multi_prompt",
            "element_list",
        ]
