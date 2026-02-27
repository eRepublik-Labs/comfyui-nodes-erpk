# ABOUTME: Dreamina V3.0 image editing request for WaveSpeed AI.
# ABOUTME: Edits a single image based on a text prompt.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class DreaminaV3Edit(BaseRequest):
    """ByteDance Dreamina V3.0 single-image editing."""

    image: str = Field(
        ..., description="URL of the image to edit."
    )
    prompt: str = Field(
        ..., description="The prompt describing desired modifications to the image."
    )
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
            "image": self.image,
            "prompt": self.prompt,
            "size": self.size,
            "seed": self.seed,
            "enable_sync_mode": self.enable_sync_mode,
            "enable_base64_output": self.enable_base64_output,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path."""
        return "/api/v3/bytedance/dreamina-v3/edit"

    def field_required(self):
        return ["image", "prompt"]

    def field_order(self):
        """Corresponds to x-order-properties in the JSON request_schema."""
        return [
            "image",
            "prompt",
            "size",
            "seed",
            "enable_sync_mode",
            "enable_base64_output",
        ]
