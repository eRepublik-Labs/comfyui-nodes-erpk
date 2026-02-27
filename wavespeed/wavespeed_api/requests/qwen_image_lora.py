# ABOUTME: Qwen Image LoRA text-to-image request for WaveSpeed AI.
# ABOUTME: Extends text-to-image with up to 3 LoRA model configurations.

from typing import Optional, List, Dict, Union
from pydantic import Field
from ..utils import BaseRequest


class QwenImageLora(BaseRequest):
    """
    Qwen Image LoRA text-to-image generation.
    Applies up to 3 LoRA models to guide image generation style and content.
    """

    prompt: str = Field(..., description="The positive prompt for the generation.")
    loras: List[Dict[str, Union[str, float]]] = Field(
        ...,
        description="LoRA configurations (max 3). Each: {path: str, scale: float 0.0-4.0}.",
        max_length=3,
    )
    size: Optional[str] = Field(
        default="1024*1024",
        description="Image dimensions in pixels (width*height format).",
    )
    seed: Optional[int] = Field(
        default=-1,
        description="Random seed; -1 generates random seed.",
        ge=-1,
        le=2147483647,
    )
    output_format: Optional[str] = Field(
        default="jpeg",
        description="Output image format: jpeg, png, or webp.",
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
            "prompt": self.prompt,
            "loras": self.loras,
            "size": self.size,
            "seed": self.seed,
            "output_format": self.output_format,
            "enable_sync_mode": self.enable_sync_mode,
            "enable_base64_output": self.enable_base64_output,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path."""
        return "/api/v3/wavespeed-ai/qwen-image/text-to-image-lora"

    def field_required(self):
        return ["prompt", "loras"]

    def field_order(self):
        return [
            "prompt",
            "loras",
            "size",
            "seed",
            "output_format",
            "enable_sync_mode",
            "enable_base64_output",
        ]
