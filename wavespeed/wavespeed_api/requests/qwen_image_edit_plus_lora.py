# ABOUTME: Qwen Image Edit Plus LoRA request for WaveSpeed AI.
# ABOUTME: Extends multi-image editing with up to 3 LoRA model configurations.

from typing import List, Dict, Union
from pydantic import Field
from .qwen_image_edit_plus import QwenImageEditPlus


class QwenImageEditPlusLora(QwenImageEditPlus):
    """
    Qwen Image Edit Plus LoRA — multi-image editing with LoRA model influences.
    Same parameters as QwenImageEditPlus plus a loras array (max 3).
    """

    loras: List[Dict[str, Union[str, float]]] = Field(
        ...,
        description="LoRA configurations (max 3). Each: {path: str, scale: float 0.0-4.0}.",
        max_length=3,
    )

    def build_payload(self) -> dict:
        payload = {
            "prompt": self.prompt,
            "images": self.images,
            "loras": self.loras,
            "size": self.size,
            "seed": self.seed,
            "output_format": self.output_format,
            "enable_base64_output": self.enable_base64_output,
            "enable_sync_mode": self.enable_sync_mode,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/wavespeed-ai/qwen-image/edit-plus-lora"

    def field_required(self):
        return ["prompt", "images", "loras"]

    def field_order(self):
        return [
            "prompt",
            "images",
            "loras",
            "size",
            "seed",
            "output_format",
            "enable_base64_output",
            "enable_sync_mode",
        ]
