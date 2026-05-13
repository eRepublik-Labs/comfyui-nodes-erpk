# ABOUTME: Seedance 2.0 text-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the bytedance/seedance-2.0 text-to-video endpoint.

from typing import List, Optional
from pydantic import Field
from ..utils import BaseRequest


class Seedance20TextToVideo(BaseRequest):
    """
    Seedance 2.0 text-to-video model.

    Generates a short video clip from a text prompt.
    """

    prompt: str = Field(..., description="Text description of the video to generate.")
    duration: Optional[int] = Field(
        default=5,
        description="Video duration in seconds.",
        ge=4,
        le=15,
    )
    aspect_ratio: Optional[str] = Field(
        default="16:9",
        description="Video aspect ratio: 16:9, 9:16, 4:3, 3:4, 1:1, or 21:9.",
    )
    resolution: Optional[str] = Field(
        default="720p",
        description="Video resolution: 480p, 720p, or 1080p. Note: Turbo tier only supports 720p and 1080p.",
    )
    reference_images: Optional[List[str]] = Field(
        default=None,
        description="Up to 4 reference image URLs for style, character, or composition guidance.",
        max_length=4,
    )
    reference_videos: Optional[List[str]] = Field(
        default=None,
        description="Up to 4 reference video URLs for motion/style guidance. Total duration should not exceed 15s.",
        max_length=4,
    )
    reference_audios: Optional[List[str]] = Field(
        default=None,
        description="Up to 4 reference audio URLs for audio style guidance. Total duration should not exceed 15s.",
        max_length=4,
    )
    enable_web_search: Optional[bool] = Field(
        default=False,
        description="Enable web search for real-time information during generation.",
    )
    generate_audio: Optional[bool] = Field(
        default=True,
        description="Generate native audio synchronized with the output video.",
    )
    seed: Optional[int] = Field(
        default=-1,
        description="Random seed; -1 generates random seed.",
        ge=-1,
        le=2147483647,
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "duration": self.duration,
            "aspect_ratio": self.aspect_ratio,
            "resolution": self.resolution,
            "reference_images": self.reference_images,
            "reference_videos": self.reference_videos,
            "reference_audios": self.reference_audios,
            "enable_web_search": self.enable_web_search,
            "generate_audio": self.generate_audio,
            "seed": self.seed,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path. Corresponds to api_path in the JSON."""
        return "/api/v3/bytedance/seedance-2.0/text-to-video"

    def field_required(self):
        return ["prompt"]

    def field_order(self):
        return [
            "prompt",
            "duration",
            "aspect_ratio",
            "resolution",
            "reference_images",
            "reference_videos",
            "reference_audios",
            "enable_web_search",
            "generate_audio",
            "seed",
        ]
