# ABOUTME: MiniMax H3 video-extend request for WaveSpeed AI.
# ABOUTME: Routes to the wavespeed-ai/minimax-h3 video-extend endpoint.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class MinimaxH3VideoExtend(BaseRequest):
    """
    MiniMax H3 video-extend model.

    Generates a new segment from the input video's last frame and appends it
    to the original. Duration and resolution describe the new segment only.
    An optional last image is the target end frame the segment interpolates
    toward. No LoRA twin exists.
    """

    prompt: str = Field(..., description="Describes the continuation: motion, scene, soundtrack.")
    video: str = Field(..., description="URL of the video to extend.")
    last_image: Optional[str] = Field(default=None, description="Target last-frame image URL or data URI for the new segment.")
    resolution: Optional[str] = Field(default="480p", description="Resolution of the new segment: 480p, 540p, 768p or 1080p.")
    duration: Optional[int] = Field(default=5, description="Length of the new segment in seconds.", ge=3, le=15)
    seed: Optional[int] = Field(default=-1, description="Random seed; a negative value generates a random seed.", ge=-1, le=2147483647)

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "video": self.video,
            "last_image": self.last_image,
            "resolution": self.resolution,
            "duration": self.duration,
            "seed": self.seed,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path. Corresponds to api_path in the JSON."""
        return "/api/v3/wavespeed-ai/minimax-h3/video-extend"

    def field_required(self):
        return ["prompt", "video"]

    def field_order(self):
        return ["prompt", "video", "last_image", "resolution", "duration", "seed"]
