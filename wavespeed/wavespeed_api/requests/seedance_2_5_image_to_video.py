# ABOUTME: Seedance 2.5 image-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the bytedance/seedance-2.5 image-to-video endpoint.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class Seedance25ImageToVideo(BaseRequest):
    """
    Seedance 2.5 image-to-video model.

    Animates a start image, optionally steering toward an ending frame. Output
    aspect ratio follows the input image, and the endpoint accepts no seed.
    """

    prompt: str = Field(..., description="Text description of the motion to generate.")
    image: str = Field(..., description="Start image URL or data URI.")
    last_image: Optional[str] = Field(
        default=None,
        description="Ending-frame image URL for continuation or ending-frame guidance.",
    )
    duration: Optional[int] = Field(
        default=5,
        description="Video duration in seconds.",
        ge=4,
        le=30,
    )
    resolution: Optional[str] = Field(
        default="720p",
        description="Video resolution: 480p, 720p, 1080p, or 4k.",
    )
    generate_audio: Optional[bool] = Field(
        default=True,
        description="Generate native audio synchronized with the output video.",
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "image": self.image,
            "last_image": self.last_image,
            "duration": self.duration,
            "resolution": self.resolution,
            "generate_audio": self.generate_audio,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path. Corresponds to api_path in the JSON."""
        return "/api/v3/bytedance/seedance-2.5/image-to-video"

    def field_required(self):
        return ["prompt", "image"]

    def field_order(self):
        return ["prompt", "image", "last_image", "duration", "resolution", "generate_audio"]
