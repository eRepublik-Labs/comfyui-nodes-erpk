# ABOUTME: Seedance 2.5 video-extend request for WaveSpeed AI.
# ABOUTME: Routes to the bytedance/seedance-2.5 video-extend endpoint.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class Seedance25VideoExtend(BaseRequest):
    """
    Seedance 2.5 video-extend model.

    Continues an existing clip past its final frame, reading up to the last 30
    seconds as context. Billing counts that context plus the new segment. The
    endpoint accepts no seed.
    """

    prompt: str = Field(..., description="Description of how the video should continue.")
    video: str = Field(..., description="Input video URL.")
    duration: Optional[int] = Field(
        default=5,
        description="Length of the new segment in seconds.",
        ge=4,
        le=30,
    )
    resolution: Optional[str] = Field(
        default="720p",
        description="Video resolution: 480p, 720p, 1080p, or 4k.",
    )
    generate_audio: Optional[bool] = Field(
        default=True,
        description="Generate audio for the new segment while preserving the original audio.",
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "video": self.video,
            "duration": self.duration,
            "resolution": self.resolution,
            "generate_audio": self.generate_audio,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path. Corresponds to api_path in the JSON."""
        return "/api/v3/bytedance/seedance-2.5/video-extend"

    def field_required(self):
        return ["prompt", "video"]

    def field_order(self):
        return ["prompt", "video", "duration", "resolution", "generate_audio"]
