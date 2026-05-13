# ABOUTME: Kling Elements creation request for WaveSpeed AI.
# ABOUTME: Produces an element ID for use in Pro variants' element_list field.

from typing import List, Optional
from pydantic import Field
from ..utils import BaseRequest


class KlingElements(BaseRequest):
    """
    Kling Elements creation model.

    Creates a consistent character/style/scene anchor (an "element") that
    can be referenced by ID from Pro variant i2v/t2v generation calls via
    the `element_list` parameter.
    """

    name: str = Field(..., max_length=20, description="Element name (≤20 chars).")
    description: str = Field(..., max_length=100, description="Element description (≤100 chars).")
    image: str = Field(..., description="Front reference image URL or base64 data URI (≥300px source, ≤10MB).")
    element_refer_list: List[str] = Field(
        ...,
        min_length=1,
        max_length=3,
        description="Additional reference image URLs / data URIs (1–3 items).",
    )
    voice_id: Optional[str] = Field(
        default=None,
        description="Bind an existing voice/tone to this element.",
    )
    tag_list: Optional[List[str]] = Field(
        default=None,
        description="Tags for organizing the element.",
    )

    def build_payload(self) -> dict:
        payload = {
            "name": self.name,
            "description": self.description,
            "image": self.image,
            "element_refer_list": self.element_refer_list,
            "voice_id": self.voice_id,
            "tag_list": self.tag_list,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/kwaivgi/kling-elements"

    def field_required(self):
        return ["name", "description", "image", "element_refer_list"]

    def field_order(self):
        return [
            "name",
            "description",
            "image",
            "element_refer_list",
            "voice_id",
            "tag_list",
        ]
