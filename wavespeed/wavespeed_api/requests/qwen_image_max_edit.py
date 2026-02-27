# ABOUTME: Qwen Image Max Edit request for WaveSpeed AI.
# ABOUTME: Accepts up to 6 reference images with no output_format, sync_mode, or base64 options.

from typing import Optional, List
from pydantic import Field
from ..utils import BaseRequest


class QwenImageMaxEdit(BaseRequest):
    """
    Qwen Image Max Edit model for multi-reference image editing
    """

    prompt: str = Field(
        ..., description="The positive prompt for the generation."
    )
    images: List[str] = Field(
        ...,
        description="Maximum of 6 reference images can be uploaded.",
        max_length=6,
    )
    size: Optional[str] = Field(
        default=None,
        description="Image dimensions in width*height format. Range: 384-3072 per dimension.",
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
            "images": self.images,
            "size": self.size,
            "seed": self.seed,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path. Corresponds to api_path in the JSON."""
        return "/api/v3/wavespeed-ai/qwen-image-max/edit"

    def field_required(self):
        return ["prompt", "images"]

    def field_order(self):
        """Corresponds to x-order-properties in the JSON request_schema."""
        return [
            "prompt",
            "images",
            "size",
            "seed",
        ]
