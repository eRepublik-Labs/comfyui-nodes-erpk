# ABOUTME: Seedance 2.5 video-edit request for WaveSpeed AI.
# ABOUTME: Routes to the bytedance/seedance-2.5 video-edit endpoint.

from typing import List, Optional
from pydantic import Field
from ..utils import BaseRequest


class Seedance25VideoEdit(BaseRequest):
    """
    Seedance 2.5 video-edit model.

    Rewrites an existing clip from a prompt. Output duration and aspect ratio
    follow the input video, so neither is a parameter; clips longer than 30s are
    trimmed and clips shorter than 4s are padded. The endpoint accepts no seed.
    """

    prompt: str = Field(..., description="Description of the edit to apply to the input video.")
    video: str = Field(..., description="Input video URL.")
    resolution: Optional[str] = Field(
        default="720p",
        description="Video resolution: 480p, 720p, 1080p, or 4k.",
    )
    reference_images: Optional[List[str]] = Field(
        default=None,
        description="Reference image URLs guiding style, identity, or appearance.",
        max_length=4,
    )
    reference_audios: Optional[List[str]] = Field(
        default=None,
        description="Reference audio URLs guiding the soundtrack or voice.",
        max_length=4,
    )
    generate_audio: Optional[bool] = Field(
        default=True,
        description="Generate audio synchronized with the edited video.",
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "video": self.video,
            "resolution": self.resolution,
            "reference_images": self.reference_images,
            "reference_audios": self.reference_audios,
            "generate_audio": self.generate_audio,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path. Corresponds to api_path in the JSON."""
        return "/api/v3/bytedance/seedance-2.5/video-edit"

    def field_required(self):
        return ["prompt", "video"]

    def field_order(self):
        return ["prompt", "video", "resolution", "reference_images", "reference_audios", "generate_audio"]
