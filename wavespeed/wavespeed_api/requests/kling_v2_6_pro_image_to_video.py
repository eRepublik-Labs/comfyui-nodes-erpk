# ABOUTME: Kling 2.6 Pro image-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the kling-v2.6-pro image-to-video endpoint with cfg_scale, end_image, and sound.

from typing import Optional
from pydantic import Field
from .kling_v2_6_std_image_to_video import KlingV2_6StdImageToVideo


class KlingV2_6ProImageToVideo(KlingV2_6StdImageToVideo):
    """
    Kling 2.6 Pro image-to-video model.

    Adds Pro-only fields on top of the Std payload: cfg_scale, end_image, and sound.
    """

    end_image: Optional[str] = Field(
        default=None,
        description="URL of the ending frame image; cannot be used together with sound.",
    )
    cfg_scale: Optional[float] = Field(
        default=0.5,
        description="Guidance scale (0.3-0.8). Higher values follow the prompt more closely.",
        ge=0.3,
        le=0.8,
    )
    sound: Optional[bool] = Field(
        default=True,
        description="Enable joint audio-video generation. Cannot be combined with end_image.",
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary including Pro-only fields."""
        payload = {
            "prompt": self.prompt,
            "image": self.image,
            "negative_prompt": self.negative_prompt,
            "end_image": self.end_image,
            "cfg_scale": self.cfg_scale,
            "sound": self.sound,
            "duration": self.duration,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/kwaivgi/kling-v2.6-pro/image-to-video"

    def field_order(self):
        return [
            "prompt",
            "image",
            "negative_prompt",
            "end_image",
            "cfg_scale",
            "sound",
            "duration",
        ]
