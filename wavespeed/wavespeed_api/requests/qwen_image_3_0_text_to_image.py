# ABOUTME: Qwen Image 3.0 and 3.0 Pro text-to-image requests for WaveSpeed AI.
# ABOUTME: Routes to the alibaba/qwen-image-3.0 (or -pro) text-to-image endpoint.

from typing import Literal
from pydantic import Field
from ..utils import BaseRequest
from .qwen_image_3_0_edit import AspectRatio


class QwenImage30TextToImage(BaseRequest):
    """Qwen Image 3.0 text-to-image model."""

    prompt: str = Field(..., min_length=1, max_length=800,
                        description="Image description in Chinese or English, up to 800 characters.")
    aspect_ratio: AspectRatio = Field(default="1:1", description="Output aspect ratio.")
    resolution: Literal["1k", "2k"] = Field(default="1k", description="Output resolution tier.")
    enable_prompt_expansion: bool = Field(default=False, description="Let the model expand the prompt.")
    seed: int = Field(default=-1, ge=-1, le=2147483647,
                      description="Random seed; -1 generates a random seed.")

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "aspect_ratio": self.aspect_ratio,
            "resolution": self.resolution,
            "enable_prompt_expansion": self.enable_prompt_expansion,
            "seed": self.seed,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self) -> str:
        """Gets the API path."""
        return "/api/v3/alibaba/qwen-image-3.0/text-to-image"

    def field_required(self):
        return ["prompt"]

    def field_order(self):
        return ["prompt", "aspect_ratio", "resolution", "enable_prompt_expansion", "seed"]


class QwenImage30ProTextToImage(QwenImage30TextToImage):
    """Qwen Image 3.0 Pro text-to-image model: same parameters, higher quality, priced per resolution tier."""

    def get_api_path(self) -> str:
        """Gets the API path."""
        return "/api/v3/alibaba/qwen-image-3.0-pro/text-to-image"
