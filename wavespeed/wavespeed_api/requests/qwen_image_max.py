# ABOUTME: Qwen Image Max text-to-image request for WaveSpeed AI.
# ABOUTME: Simplified payload with no output_format, sync_mode, or base64 options.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class QwenImageMax(BaseRequest):
    """
    Qwen Image Max text-to-image model
    """

    prompt: str = Field(
        ..., description="The positive prompt for the generation (max 800 chars)."
    )
    size: Optional[str] = Field(
        default="1024*1024",
        description="Image dimensions in width*height format. Range: 256-1536 per dimension.",
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
            "size": self.size,
            "seed": self.seed,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path. Corresponds to api_path in the JSON."""
        return "/api/v3/wavespeed-ai/qwen-image-max/text-to-image"

    def field_required(self):
        return ["prompt"]

    def field_order(self):
        """Corresponds to x-order-properties in the JSON request_schema."""
        return [
            "prompt",
            "size",
            "seed",
        ]
