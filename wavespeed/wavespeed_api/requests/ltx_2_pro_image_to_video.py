# ABOUTME: LTX 2 Pro image-to-video request via WaveSpeed.
# ABOUTME: Routes to the /api/v3/lightricks/ltx-2-pro/image-to-video endpoint.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class Ltx2ProImageToVideo(BaseRequest):
    """
    Lightricks LTX 2 Pro image-to-video model.
    Animates a source image into short-form video with optional audio.
    """

    image: str = Field(..., description="Source image URL.")
    prompt: str = Field(..., max_length=5000, description="Positive prompt for generation.")
    duration: Optional[int] = Field(
        default=6,
        description="Output duration in seconds. Valid values: 6, 8, 10.",
    )
    generate_audio: Optional[bool] = Field(
        default=True,
        description="Whether to include audio in the output.",
    )

    def build_payload(self) -> dict:
        payload = {
            "image": self.image,
            "prompt": self.prompt,
            "duration": self.duration,
            "generate_audio": self.generate_audio,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/lightricks/ltx-2-pro/image-to-video"

    def field_required(self):
        return ["image", "prompt"]

    def field_order(self):
        return ["image", "prompt", "duration", "generate_audio"]
