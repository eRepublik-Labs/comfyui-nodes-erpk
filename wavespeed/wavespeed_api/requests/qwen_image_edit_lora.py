# ABOUTME: Qwen Image Edit LoRA request for WaveSpeed AI.
# ABOUTME: Extends single-image editing with up to 3 LoRA model configurations.

from typing import List, Dict, Union
from pydantic import Field
from .qwen_image_edit import QwenImageEdit


class QwenImageEditLora(QwenImageEdit):
    """
    Qwen Image Edit LoRA — single-image editing with LoRA model influences.
    Same parameters as QwenImageEdit plus a loras array (max 3).
    """

    loras: List[Dict[str, Union[str, float]]] = Field(
        ...,
        description="LoRA configurations (max 3). Each: {path: str, scale: float 0.0-4.0}.",
        max_length=3,
    )

    def build_payload(self) -> dict:
        payload = {
            "prompt": self.prompt,
            "image": self.image,
            "loras": self.loras,
            "size": self.size,
            "seed": self.seed,
            "output_format": self.output_format,
            "enable_base64_output": self.enable_base64_output,
            "enable_sync_mode": self.enable_sync_mode,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/wavespeed-ai/qwen-image/edit-lora"

    def field_required(self):
        return ["prompt", "image", "loras"]

    def field_order(self):
        return [
            "prompt",
            "image",
            "loras",
            "size",
            "seed",
            "output_format",
            "enable_base64_output",
            "enable_sync_mode",
        ]
