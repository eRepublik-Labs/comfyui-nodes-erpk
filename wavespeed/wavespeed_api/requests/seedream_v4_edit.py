from typing import Optional, List
from pydantic import Field
from ..utils import BaseRequest


class SeedreamV4Edit(BaseRequest):
    """
    ByteDance Seedream V4 Edit image editing model
    """

    prompt: str = Field(
        ..., description="The prompt describing desired modifications to the image."
    )

    images: List[str] = Field(
        ...,
        description="The images to edit. A maximum of 10 reference images can be uploaded..",
        max_items=10,
    )

    size: Optional[str] = Field(
        default="2048*2048",
        description="The size of the generated media, supporting up to 4K resolution for images. If you need to match the size of an existing image, you must explicitly specify the dimensions, as automatic resizing to match the image is not supported.",
    )

    enable_sync_mode: Optional[bool] = Field(
        default=False,
        description="If set to true, the function will wait for the result to be generated and uploaded before returning the response. It allows you to get the result directly in the response. This property is only available through the API.",
    )

    enable_base64_output: Optional[bool] = Field(
        default=False,
        description="If enabled, the output will be encoded into a BASE64 string instead of a URL. This property is only available through the API.",
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "images": self.images,
            "size": self.size,
            "enable_sync_mode": self.enable_sync_mode,
            "enable_base64_output": self.enable_base64_output,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path. Corresponds to api_path in the JSON."""
        return "/api/v3/bytedance/seedream-v4/edit"

    def field_required(self):
        return ["image", "prompt"]

    def field_order(self):
        """Corresponds to x-order-properties in the JSON request_schema."""
        return ["image", "prompt", "size", "enable_sync_mode", "enable_base64_output"]
