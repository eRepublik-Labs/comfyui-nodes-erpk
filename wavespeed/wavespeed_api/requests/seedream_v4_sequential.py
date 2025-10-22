from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class SeedreamV4Sequential(BaseRequest):
    """
    ByteDance Seedream-V4 Sequential text to image model
    Enables multi-image generation with cross-image consistency
    """

    prompt: str = Field(..., description="The prompt to generate images from.")

    max_images: int = Field(
        ...,
        description="Number of images to generate (1-15). Must match the quantity specified in your prompt text.",
        ge=1,
        le=15,
    )

    size: Optional[str] = Field(
        default="2048*2048",
        description="The size of the generated image, supporting up to 4K resolution. Format: width*height (1024-4096 per dimension).",
    )

    enable_sync_mode: Optional[bool] = Field(
        default=False,
        description="If set to true, the function will wait for the result to be generated and uploaded before returning the response.",
    )

    enable_base64_output: Optional[bool] = Field(
        default=False,
        description="If enabled, the output will be encoded into a BASE64 string instead of a URL.",
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "max_images": self.max_images,
            "size": self.size,
            "enable_sync_mode": self.enable_sync_mode,
            "enable_base64_output": self.enable_base64_output,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path."""
        return "/api/v3/bytedance/seedream-v4/sequential"

    def field_required(self):
        return ["prompt", "max_images"]

    def field_order(self):
        """Corresponds to x-order-properties in the JSON request_schema."""
        return ["prompt", "max_images", "size", "enable_sync_mode", "enable_base64_output"]
