# ABOUTME: Qwen Image Multiple Angles request for angle-based image editing via WaveSpeed AI.
# ABOUTME: Rotates/repositions subjects in images using horizontal, vertical angles and distance.

from typing import Optional, List
from pydantic import Field
from ..utils import BaseRequest


class QwenImageMultipleAngles(BaseRequest):
    """
    Qwen Image Multiple Angles (edit-2509) for angle-based image transformation.
    Adjusts viewing angle and distance of subjects in reference images.
    """

    images: List[str] = Field(
        ...,
        description="Reference images to transform. Maximum of 3 images.",
        max_length=3,
    )
    prompt: Optional[str] = Field(
        default=None,
        description="Optional text description to guide the transformation.",
    )
    horizontal_angle: Optional[int] = Field(
        default=None,
        description="Horizontal rotation angle (-90 to 90 degrees).",
        ge=-90,
        le=90,
    )
    vertical_angle: Optional[int] = Field(
        default=None,
        description="Vertical rotation angle (-30 to 60 degrees).",
        ge=-30,
        le=60,
    )
    distance: Optional[float] = Field(
        default=None,
        description="Subject distance factor (0 to 2, default 1).",
        ge=0,
        le=2,
    )
    size: Optional[str] = Field(
        default=None,
        description="Output dimensions (width*height). Range: 256-1536 per dimension.",
    )
    seed: Optional[int] = Field(
        default=-1,
        description="Random seed; -1 generates random seed.",
        ge=-1,
        le=2147483647,
    )
    output_format: Optional[str] = Field(
        default="jpeg",
        description="Output image format: jpeg, png, or webp.",
    )
    enable_sync_mode: Optional[bool] = Field(
        default=False,
        description="Waits for completion before responding.",
    )
    enable_base64_output: Optional[bool] = Field(
        default=False,
        description="Returns BASE64-encoded output instead of URL.",
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "images": self.images,
            "prompt": self.prompt,
            "horizontal_angle": self.horizontal_angle,
            "vertical_angle": self.vertical_angle,
            "distance": self.distance,
            "size": self.size,
            "seed": self.seed,
            "output_format": self.output_format,
            "enable_sync_mode": self.enable_sync_mode,
            "enable_base64_output": self.enable_base64_output,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path."""
        return "/api/v3/wavespeed-ai/qwen-image/edit-2509-multiple-angles"

    def field_required(self):
        return ["images"]

    def field_order(self):
        return [
            "images",
            "prompt",
            "horizontal_angle",
            "vertical_angle",
            "distance",
            "size",
            "seed",
            "output_format",
            "enable_sync_mode",
            "enable_base64_output",
        ]
