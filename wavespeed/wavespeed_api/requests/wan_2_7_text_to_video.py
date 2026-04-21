# ABOUTME: Alibaba WAN 2.7 text-to-video request for WaveSpeed AI.
# ABOUTME: Routes to /api/v3/alibaba/wan-2.7/text-to-video.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class Wan27TextToVideo(BaseRequest):
    """
    Alibaba WAN 2.7 text-to-video model.
    """

    prompt: str = Field(..., description="The positive prompt for video generation.")
    negative_prompt: Optional[str] = Field(
        default=None, description="Elements to exclude from the generated video."
    )
    audio: Optional[str] = Field(
        default=None, description="Optional audio URL used to guide generation."
    )
    resolution: Optional[str] = Field(
        default="720p", description="Output resolution: 720p or 1080p."
    )
    aspect_ratio: Optional[str] = Field(
        default="16:9",
        description="Output aspect ratio: 16:9, 9:16, 1:1, 4:3, or 3:4.",
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
            "negative_prompt": self.negative_prompt,
            "audio": self.audio,
            "resolution": self.resolution,
            "aspect_ratio": self.aspect_ratio,
            "duration": self.duration,
            "enable_prompt_expansion": self.enable_prompt_expansion,
            "seed": self.seed,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/alibaba/wan-2.7/text-to-video"

    def field_required(self):
        return ["prompt"]

    def field_order(self):
        return [
            "prompt",
            "negative_prompt",
            "audio",
            "resolution",
            "aspect_ratio",
            "duration",
            "enable_prompt_expansion",
            "seed",
        ]
