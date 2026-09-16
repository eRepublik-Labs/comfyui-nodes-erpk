# ABOUTME: MiniMax H3 reference-to-video request for WaveSpeed AI.
# ABOUTME: Routes to MiniMax's own minimax/h3 reference-to-video endpoint.

from typing import List, Optional
from pydantic import Field
from ..utils import BaseRequest


class MinimaxH3ReferenceToVideo(BaseRequest):
    """
    MiniMax H3 reference-to-video model, MiniMax-hosted edition.

    Generates video guided by reference images, videos, and audio. The prompt
    must cite each reference with bracket tags such as `<Picture 1>`, `<Video 1>`
    and `<Audio 1>`; plain-text mentions are ignored. At least one reference
    image or video is required, and audio cannot be supplied alone. The
    endpoint documents no seed.
    """

    prompt: str = Field(..., description="Prompt citing references as <Picture N>, <Video N>, <Audio N>.")
    reference_images: Optional[List[str]] = Field(
        default=None,
        description="Reference image URLs, cited as <Picture 1> through <Picture 9>. First 5 free, then $0.05 each.",
        max_length=9,
    )
    reference_videos: Optional[List[str]] = Field(
        default=None,
        description="Reference video URLs, cited as <Video 1> through <Video 3>. Each normalised to 2-15s; combined duration capped at 15s and billed per second.",
        max_length=3,
    )
    reference_audios: Optional[List[str]] = Field(
        default=None,
        description="Reference audio URLs, cited as <Audio 1> through <Audio 3>. Cannot be supplied alone.",
        max_length=3,
    )
    aspect_ratio: Optional[str] = Field(
        default="16:9",
        description="Video aspect ratio: 21:9, 16:9, 4:3, 1:1, 3:4, or 9:16.",
    )
    resolution: Optional[str] = Field(
        default="768p",
        description="Video resolution: 768p or 2k.",
    )
    duration: Optional[int] = Field(
        default=5,
        description="Video duration in seconds.",
        ge=4,
        le=15,
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "reference_images": self.reference_images,
            "reference_videos": self.reference_videos,
            "reference_audios": self.reference_audios,
            "aspect_ratio": self.aspect_ratio,
            "resolution": self.resolution,
            "duration": self.duration,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path. Corresponds to api_path in the JSON."""
        return "/api/v3/minimax/h3/reference-to-video"

    def field_required(self):
        return ["prompt"]

    def field_order(self):
        return [
            "prompt",
            "reference_images",
            "reference_videos",
            "reference_audios",
            "aspect_ratio",
            "resolution",
            "duration",
        ]
