# ABOUTME: Alibaba WAN 2.7 image-to-video request for WaveSpeed AI.
# ABOUTME: Routes to /api/v3/alibaba/wan-2.7/image-to-video.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class Wan27ImageToVideo(BaseRequest):
    """
    Alibaba WAN 2.7 image-to-video model.
    """

    prompt: str = Field(..., description="The positive prompt for video generation.")
    image: str = Field(..., description="First frame image (URL).")
    last_image: Optional[str] = Field(
        default=None, description="Optional end frame image (URL)."
    )
    audio: Optional[str] = Field(
        default=None, description="Optional audio URL used to guide generation."
    )
    negative_prompt: Optional[str] = Field(
        default=None, description="Elements to exclude from the generated video."
    )
    resolution: Optional[str] = Field(
        default="720p", description="Output resolution: 720p or 1080p."
    )
    duration: Optional[int] = Field(
        default=5,
        description="Clip length in seconds (2-15).",
        ge=2,
        le=15,
    )
    enable_prompt_expansion: Optional[bool] = Field(
        default=False,
        description="Automatically enrich the prompt before generation.",
    )
    seed: Optional[int] = Field(
        default=-1,
        description="Random seed; -1 generates a random seed.",
        ge=-1,
        le=2147483647,
    )

    def build_payload(self) -> dict:
        payload = {
            "prompt": self.prompt,
            "image": self.image,
            "last_image": self.last_image,
            "audio": self.audio,
            "negative_prompt": self.negative_prompt,
            "resolution": self.resolution,
            "duration": self.duration,
            "enable_prompt_expansion": self.enable_prompt_expansion,
            "seed": self.seed,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/alibaba/wan-2.7/image-to-video"

    def field_required(self):
        return ["prompt", "image"]

    def field_order(self):
        return [
            "prompt",
            "image",
            "last_image",
            "audio",
            "negative_prompt",
            "resolution",
            "duration",
            "enable_prompt_expansion",
            "seed",
        ]
