from typing import Optional
from pydantic import Field
from ..utils import BaseRequest


class SeedreamV4(BaseRequest):
    """
    ByteDance Seedream-V4 text to image model
    """

    prompt: str = Field(..., description="The prompt to generate an image from.")
    width: Optional[int] = Field(
        default=2048, description="The width of the generated image.", ge=0, le=4096
    )
    height: Optional[int] = Field(
        default=2048, description="The height of the generated image.", ge=0, le=4096
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "size": f"{self.width}*{self.height}",
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path. Corresponds to api_path in the JSON."""
        return "/api/v3/bytedance/seedream-v4"

    def field_required(self):
        return ["prompt"]

    def field_order(self):
        """Corresponds to x-order-properties in the JSON request_schema."""
        return ["prompt", "size"]
