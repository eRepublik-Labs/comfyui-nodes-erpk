# ABOUTME: MiniMax H3 text-to-image request for WaveSpeed AI.
# ABOUTME: Routes to the wavespeed-ai/minimax-h3 text-to-image endpoint, or its -lora twin.

from typing import Dict, List, Optional, Union
from pydantic import Field
from ..utils import BaseRequest


class MinimaxH3TextToImage(BaseRequest):
    """
    MiniMax H3 text-to-image model.

    Generates a single image at 1k (~1MP) or 2k (~4MP) in one of fifteen
    aspect ratios. Supplying LoRAs switches the call to the -lora twin.
    """

    prompt: str = Field(..., description="Text description of the desired image.")
    aspect_ratio: Optional[str] = Field(default="1:1", description="Output aspect ratio.")
    resolution: Optional[str] = Field(default="1k", description="Output resolution: 1k or 2k.")
    output_format: Optional[str] = Field(default="jpeg", description="Output image format: jpeg, png or webp.")
    loras: Optional[List[Dict[str, Union[str, float]]]] = Field(
        default=None,
        description="Up to 3 LoRA weights as {path, scale}; routes the call to the -lora twin.",
        max_length=3,
    )
    seed: Optional[int] = Field(
        default=-1,
        description="Random seed; -1 generates a random seed.",
        ge=-1,
        le=2147483647,
    )
    enable_base64_output: Optional[bool] = Field(default=False, description="Return base64 instead of a URL.")
    enable_sync_mode: Optional[bool] = Field(default=False, description="Wait for the result inline.")

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "aspect_ratio": self.aspect_ratio,
            "resolution": self.resolution,
            "output_format": self.output_format,
            "loras": self.loras,
            "seed": self.seed,
            "enable_base64_output": self.enable_base64_output,
            "enable_sync_mode": self.enable_sync_mode,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path. Corresponds to api_path in the JSON."""
        if self.loras:
            return "/api/v3/wavespeed-ai/minimax-h3/text-to-image-lora"
        return "/api/v3/wavespeed-ai/minimax-h3/text-to-image"

    def field_required(self):
        return ["prompt"]

    def field_order(self):
        return ["prompt", "aspect_ratio", "resolution", "output_format", "loras", "seed",
                "enable_base64_output", "enable_sync_mode"]
