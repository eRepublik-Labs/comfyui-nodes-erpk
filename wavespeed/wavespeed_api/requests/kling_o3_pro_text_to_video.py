# ABOUTME: Kling O3 Pro text-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the kling-video-o3-pro endpoint and adds the element_list field.

from typing import List, Optional
from pydantic import Field
from .kling_o3_text_to_video import KlingO3TextToVideo


class KlingO3ProTextToVideo(KlingO3TextToVideo):
    """
    Kling O3 Pro text-to-video model.

    Adds Pro-only fields on top of the Std payload: element_list for locking
    pre-generated visual elements across the clip.
    """

    element_list: Optional[List[dict]] = Field(
        default=None,
        description="Pre-generated element IDs for visual consistency across scenes.",
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary including Pro-only fields."""
        payload = {
            "prompt": self.prompt,
            "duration": self.duration,
            "aspect_ratio": self.aspect_ratio,
            "sound": self.sound,
            "shot_type": self.shot_type,
            "multi_prompt": self.multi_prompt,
            "element_list": self.element_list,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/kwaivgi/kling-video-o3-pro/text-to-video"

    def field_order(self):
        return [
            "prompt",
            "duration",
            "aspect_ratio",
            "sound",
            "shot_type",
            "multi_prompt",
            "element_list",
        ]
