# ABOUTME: Kling O3 Pro image-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the kling-video-o3-pro endpoint and adds element_list on top of the Std payload.

from typing import List, Optional
from pydantic import Field
from .kling_o3_image_to_video import KlingO3ImageToVideo


class KlingO3ProImageToVideo(KlingO3ImageToVideo):
    """
    Kling O3 Pro image-to-video model.

    Adds Pro-only fields on top of the Std payload: element_list for locking
    visual elements across the clip. Pro documents duration as 5 or 10 only.
    """

    element_list: Optional[List[dict]] = Field(
        default=None,
        description="Element IDs from Kling Elements to lock for visual consistency throughout the clip.",
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary including Pro-only fields."""
        payload = {
            "prompt": self.prompt,
            "image": self.image,
            "end_image": self.end_image,
            "duration": self.duration,
            "sound": self.sound,
            "shot_type": self.shot_type,
            "multi_prompt": self.multi_prompt,
            "element_list": self.element_list,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/kwaivgi/kling-video-o3-pro/image-to-video"

    def field_order(self):
        return [
            "prompt",
            "image",
            "end_image",
            "duration",
            "sound",
            "shot_type",
            "multi_prompt",
            "element_list",
        ]
