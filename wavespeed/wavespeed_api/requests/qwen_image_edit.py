from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class QwenImageEdit(BaseRequest):
    """
    Qwen Image Edit model for image editing based on text prompts
    """

    prompt: str = Field(
        ..., description="The positive prompt for the generation."
    )
    image: str = Field(
        ..., description="The image to generate an image from."
    )
    size: Optional[str] = Field(
        default=None,
        description="Output dimensions (width×height). Range: 256-1536 per dimension.",
    )
    seed: Optional[int] = Field(
        default=-1,
        description="Random seed; -1 generates random seed.",
        ge=-1,
        le=2147483647,
    )
    output_format: Optional[str] = Field(
        default="jpeg", description="Image format: jpeg, png, or webp."
    )
    enable_base64_output: Optional[bool] = Field(
        default=False,
        description="Returns BASE64 instead of URL.",
    )
    enable_sync_mode: Optional[bool] = Field(
        default=False,
        description="Waits for completion before responding.",
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "image": self.image,
            "size": self.size,
            "seed": self.seed,
            "output_format": self.output_format,
            "enable_base64_output": self.enable_base64_output,
            "enable_sync_mode": self.enable_sync_mode,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path. Corresponds to api_path in the JSON."""
        return "/api/v3/wavespeed-ai/qwen-image/edit"

    def field_required(self):
        return ["prompt", "image"]

    def field_order(self):
        """Corresponds to x-order-properties in the JSON request_schema."""
        return [
            "prompt",
            "image",
            "size",
            "seed",
            "output_format",
            "enable_base64_output",
            "enable_sync_mode",
        ]
