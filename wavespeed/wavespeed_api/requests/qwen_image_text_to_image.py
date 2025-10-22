from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class QwenImageTextToImage(BaseRequest):
    """
    Qwen Image text-to-image model
    """

    prompt: str = Field(..., description="The positive prompt for the generation.")
    size: Optional[str] = Field(
        default="1024*1024",
        description="Image dimensions in pixels (width*height format). Max resolution: 1536×1536 pixels.",
    )
    seed: Optional[int] = Field(
        default=-1,
        description="Random seed; -1 generates random seed.",
        ge=-1,
        le=2147483647,
    )
    output_format: Optional[str] = Field(
        default="jpeg", description="Output image format: jpeg, png, or webp."
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
            "output_format": self.output_format,
            "enable_sync_mode": self.enable_sync_mode,
            "enable_base64_output": self.enable_base64_output,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path. Corresponds to api_path in the JSON."""
        return "/api/v3/wavespeed-ai/qwen-image/text-to-image"

    def field_required(self):
        return ["prompt"]

    def field_order(self):
        """Corresponds to x-order-properties in the JSON request_schema."""
        return [
            "prompt",
            "size",
            "seed",
            "output_format",
            "enable_sync_mode",
            "enable_base64_output",
        ]
