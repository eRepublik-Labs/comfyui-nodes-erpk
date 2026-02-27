# ABOUTME: Dreamina V3.0 text-to-image request for WaveSpeed AI.
# ABOUTME: Generates images from text prompts with optional prompt expansion.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class DreaminaV3TextToImage(BaseRequest):
    """ByteDance Dreamina V3.0 text-to-image generation."""

    prompt: str = Field(..., description="The positive prompt for the generation.")
    size: Optional[str] = Field(
        default="1328*1328",
        description="Image dimensions in pixels (width*height format). Range: 512-2048px.",
    )
    seed: Optional[int] = Field(
        default=-1,
        description="Random seed; -1 generates random seed.",
        ge=-1,
        le=2147483647,
    )
    enable_prompt_expansion: Optional[bool] = Field(
        default=True,
        description="Automatically expand and enhance the prompt for better results.",
    )
    enable_sync_mode: Optional[bool] = Field(
        default=False,
        description="If set to true, waits for completion before returning response.",
    )
    enable_base64_output: Optional[bool] = Field(
        default=False,
        description="If enabled, returns BASE64-encoded output instead of URL.",
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "size": self.size,
            "seed": self.seed,
            "enable_prompt_expansion": self.enable_prompt_expansion,
            "enable_sync_mode": self.enable_sync_mode,
            "enable_base64_output": self.enable_base64_output,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path."""
        return "/api/v3/bytedance/dreamina-v3/text-to-image"

    def field_required(self):
        return ["prompt"]

    def field_order(self):
        """Corresponds to x-order-properties in the JSON request_schema."""
        return [
            "prompt",
            "size",
            "seed",
            "enable_prompt_expansion",
            "enable_sync_mode",
            "enable_base64_output",
        ]
