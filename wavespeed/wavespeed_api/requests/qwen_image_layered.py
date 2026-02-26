# ABOUTME: Qwen Image Layered request for image layer decomposition via WaveSpeed AI.
# ABOUTME: Decomposes a single image into N RGBA layers for compositing workflows.

from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class QwenImageLayered(BaseRequest):
    """
    Qwen Image Layered decomposition.
    Splits a single image into 2-8 RGBA layers with transparency.
    """

    image: str = Field(
        ..., description="The image to decompose into layers."
    )
    prompt: Optional[str] = Field(
        default=None,
        description="Optional text description to guide layer decomposition.",
    )
    num_layers: Optional[int] = Field(
        default=4,
        description="Number of layers to decompose into (2-8).",
        ge=2,
        le=8,
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
            "image": self.image,
            "prompt": self.prompt,
            "num_layers": self.num_layers,
            "enable_sync_mode": self.enable_sync_mode,
            "enable_base64_output": self.enable_base64_output,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path."""
        return "/api/v3/wavespeed-ai/qwen-image/layered"

    def field_required(self):
        return ["image"]

    def field_order(self):
        return [
            "image",
            "prompt",
            "num_layers",
            "enable_sync_mode",
            "enable_base64_output",
        ]
