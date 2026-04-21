# ABOUTME: Veo 3.1 image-to-video request billed via WaveSpeed.
# ABOUTME: Routes to the /api/v3/google/veo3.1/image-to-video endpoint.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class WaveSpeedVeo31ImageToVideo(BaseRequest):
    """
    Google Veo 3.1 image-to-video model billed through WaveSpeed.
    Generates video starting from an input image with synchronized native audio.
    """

    prompt: str = Field(..., description="The text prompt describing the motion/scene.")
    image: str = Field(..., description="URL of the input image (JPEG/PNG/WEBP).")
    last_image: Optional[str] = Field(
        default=None,
        description="Optional end-frame image URL for interpolation.",
    )
    aspect_ratio: Optional[str] = Field(
        default="16:9",
        description="Video aspect ratio: 16:9 (landscape) or 9:16 (portrait).",
    )
    duration: Optional[int] = Field(
        default=8,
        description="Video duration in seconds. Veo 3.1 supports 4, 6, 8.",
        ge=4,
        le=8,
    )
    resolution: Optional[str] = Field(
        default="1080p",
        description="Output resolution: 720p or 1080p.",
    )
    generate_audio: Optional[bool] = Field(
        default=True,
        description="Whether to generate synchronized native audio.",
    )
    negative_prompt: Optional[str] = Field(
        default=None,
        description="Elements to exclude from the generated video.",
    )
    seed: Optional[int] = Field(
        default=-1,
        description="Random seed; -1 generates a random seed.",
        ge=-1,
        le=2147483647,
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "image": self.image,
            "last_image": self.last_image,
            "aspect_ratio": self.aspect_ratio,
            "duration": self.duration,
            "resolution": self.resolution,
            "generate_audio": self.generate_audio,
            "negative_prompt": self.negative_prompt,
            "seed": self.seed,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/google/veo3.1/image-to-video"

    def field_required(self):
        return ["prompt", "image"]

    def field_order(self):
        return [
            "prompt",
            "image",
            "last_image",
            "aspect_ratio",
            "duration",
            "resolution",
            "generate_audio",
            "negative_prompt",
            "seed",
        ]
