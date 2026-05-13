# ABOUTME: Seedance 2.0 image-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the bytedance/seedance-2.0 image-to-video endpoint.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class Seedance20ImageToVideo(BaseRequest):
    """
    Seedance 2.0 image-to-video model.

    Animates a source image into a short video clip driven by a text prompt.
    Supports an optional end-frame image for video continuation.
    """

    prompt: str = Field(..., description="Text description of the desired motion.")
    image: str = Field(..., description="Start frame image URL to guide the video generation.")
    last_image: Optional[str] = Field(
        default=None,
        description="End frame image URL for video continuation.",
    )
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
            "image": self.image,
            "last_image": self.last_image,
            "duration": self.duration,
            "aspect_ratio": self.aspect_ratio,
            "resolution": self.resolution,
            "enable_web_search": self.enable_web_search,
            "generate_audio": self.generate_audio,
            "seed": self.seed,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path. Corresponds to api_path in the JSON."""
        return "/api/v3/bytedance/seedance-2.0/image-to-video"

    def field_required(self):
        return ["prompt", "image"]

    def field_order(self):
        return [
            "prompt",
            "image",
            "last_image",
            "duration",
            "aspect_ratio",
            "resolution",
            "enable_web_search",
            "generate_audio",
            "seed",
        ]
