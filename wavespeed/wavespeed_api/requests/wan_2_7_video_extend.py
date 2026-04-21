# ABOUTME: Alibaba WAN 2.7 video-extend request for WaveSpeed AI.
# ABOUTME: Routes to /api/v3/alibaba/wan-2.7/video-extend; extends an existing source clip.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class Wan27VideoExtend(BaseRequest):
    """
    Alibaba WAN 2.7 video-extend model.

    Takes a source video URL and a continuation prompt; returns a longer clip.
    """

    prompt: str = Field(..., description="The positive prompt describing the continuation.")
    video: str = Field(..., description="Source video URL to extend.")
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
        description="Length of the extension in seconds (5-15).",
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
            "video": self.video,
            "audio": self.audio,
            "negative_prompt": self.negative_prompt,
            "resolution": self.resolution,
            "duration": self.duration,
            "enable_prompt_expansion": self.enable_prompt_expansion,
            "seed": self.seed,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/alibaba/wan-2.7/video-extend"

    def field_required(self):
        return ["prompt", "video"]

    def field_order(self):
        return [
            "prompt",
            "video",
            "audio",
            "negative_prompt",
            "resolution",
            "duration",
            "enable_prompt_expansion",
            "seed",
        ]
