# ABOUTME: MiniMax H3 image-edit request for WaveSpeed AI.
# ABOUTME: Routes to the wavespeed-ai/minimax-h3 image-edit endpoint, or its -lora twin.

from typing import Dict, List, Optional, Union
from pydantic import Field
from ..utils import BaseRequest


class MinimaxH3ImageEdit(BaseRequest):
    """
    MiniMax H3 image-edit model.

    Re-renders a subject from 1 to 9 reference images into a new scene, outfit
    or style from an instruction, preserving identity. The prompt cites each
    reference as `<Picture N>`. An unset aspect ratio follows the first
    reference. Supplying LoRAs switches the call to the -lora twin.
    """

    prompt: str = Field(..., description="Edit instruction, citing references as <Picture 1> through <Picture 9>.")
    images: List[str] = Field(..., description="Reference image URLs or data URIs (1-9).", min_length=1, max_length=9)
    aspect_ratio: Optional[str] = Field(default=None, description="Output aspect ratio; unset follows the first reference image.")
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
            "images": self.images,
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
            return "/api/v3/wavespeed-ai/minimax-h3/image-edit-lora"
        return "/api/v3/wavespeed-ai/minimax-h3/image-edit"

    def field_required(self):
        return ["prompt", "images"]

    def field_order(self):
        return ["prompt", "images", "aspect_ratio", "resolution", "output_format", "loras", "seed",
                "enable_base64_output", "enable_sync_mode"]
