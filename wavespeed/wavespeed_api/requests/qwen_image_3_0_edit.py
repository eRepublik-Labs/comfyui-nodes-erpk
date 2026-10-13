# ABOUTME: Qwen Image 3.0 and 3.0 Pro edit requests for WaveSpeed AI.
# ABOUTME: Routes to the alibaba/qwen-image-3.0 (or -pro) edit endpoint.

from typing import List, Literal, Optional
from pydantic import Field
from ..utils import BaseRequest

AspectRatio = Literal["1:1", "1:2", "2:1", "1:3", "3:1", "2:3", "3:2", "3:4", "4:3",
                      "4:5", "5:4", "9:16", "16:9", "9:21", "21:9"]


class QwenImage30Edit(BaseRequest):
    """
    Qwen Image 3.0 edit model.

    Edits 1 to 3 reference images from an instruction. An unset aspect ratio
    follows the first reference image.
    """

    prompt: str = Field(..., min_length=1, max_length=800,
                        description="Edit instruction in Chinese or English, up to 800 characters.")
    images: List[str] = Field(..., min_length=1, max_length=3,
                              description="Reference image URLs or data URIs (1-3), 384-2048 px per side.")
    aspect_ratio: Optional[AspectRatio] = Field(
        default=None, description="Output aspect ratio; unset follows the first reference image.")
    resolution: Literal["1k", "2k"] = Field(default="1k", description="Output resolution tier.")
    enable_prompt_expansion: bool = Field(default=False, description="Let the model expand the prompt.")
    seed: int = Field(default=-1, ge=-1, le=2147483647,
                      description="Random seed; -1 generates a random seed.")

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "images": self.images,
            "aspect_ratio": self.aspect_ratio,
            "resolution": self.resolution,
            "enable_prompt_expansion": self.enable_prompt_expansion,
            "seed": self.seed,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self) -> str:
        """Gets the API path."""
        return "/api/v3/alibaba/qwen-image-3.0/edit"

    def field_required(self):
        return ["prompt", "images"]

    def field_order(self):
        return ["prompt", "images", "aspect_ratio", "resolution", "enable_prompt_expansion", "seed"]


class QwenImage30ProEdit(QwenImage30Edit):
    """Qwen Image 3.0 Pro edit model: same parameters, higher quality, priced per resolution tier."""

    def get_api_path(self) -> str:
        """Gets the API path."""
        return "/api/v3/alibaba/qwen-image-3.0-pro/edit"
