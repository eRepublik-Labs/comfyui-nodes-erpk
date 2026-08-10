# ABOUTME: Seedance 2.5 text-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the bytedance/seedance-2.5 text-to-video endpoint.

from typing import List, Optional
from pydantic import Field
from ..utils import BaseRequest


class Seedance25TextToVideo(BaseRequest):
    """
    Seedance 2.5 text-to-video model.

    Generates a video clip from a text prompt, optionally guided by reference
    images, videos, or audio. The endpoint accepts no seed.
    """

    prompt: str = Field(..., description="Text description of the video to generate.")
    duration: Optional[int] = Field(
        default=5,
        description="Video duration in seconds.",
        ge=4,
        le=30,
    )
    aspect_ratio: Optional[str] = Field(
        default="16:9",
        description="Video aspect ratio: 16:9, 9:16, 4:3, 3:4, 1:1, or 21:9.",
    )
    resolution: Optional[str] = Field(
        default="720p",
        description="Video resolution: 480p, 720p, 1080p, or 4k.",
    )
    reference_images: Optional[List[str]] = Field(
        default=None,
        description="Reference image URLs guiding style, character, or composition.",
        max_length=4,
    )
    reference_videos: Optional[List[str]] = Field(
        default=None,
        description="Reference video URLs guiding motion and pacing. Total duration up to 30s.",
        max_length=4,
    )
    reference_audios: Optional[List[str]] = Field(
        default=None,
        description="Reference audio URLs guiding the soundtrack. Total duration up to 30s.",
        max_length=4,
    )
    generate_audio: Optional[bool] = Field(
        default=True,
        description="Generate native audio synchronized with the output video.",
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
            "generate_audio": self.generate_audio,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path. Corresponds to api_path in the JSON."""
        return "/api/v3/bytedance/seedance-2.5/text-to-video"

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
            "generate_audio",
        ]
