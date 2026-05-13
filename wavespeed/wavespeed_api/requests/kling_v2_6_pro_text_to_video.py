# ABOUTME: Kling 2.6 Pro text-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the kling-v2.6-pro text-to-video endpoint with cfg_scale and sound.

from typing import Optional
from pydantic import Field
from .kling_v2_6_std_text_to_video import KlingV2_6StdTextToVideo


class KlingV2_6ProTextToVideo(KlingV2_6StdTextToVideo):
    """
    Kling 2.6 Pro text-to-video model.

    Adds Pro-only fields on top of the Std payload: cfg_scale and sound.
    """

    cfg_scale: Optional[float] = Field(
        default=0.5,
        description="Guidance scale (0.0-1.0). Higher values follow the prompt more closely.",
        ge=0.0,
        le=1.0,
    )
    sound: Optional[bool] = Field(
        default=True,
        description="Enable joint audio-video generation.",
    )

    def build_payload(self) -> dict:
        """Builds the request payload dictionary including Pro-only fields."""
        payload = {
            "prompt": self.prompt,
            "negative_prompt": self.negative_prompt,
            "aspect_ratio": self.aspect_ratio,
            "cfg_scale": self.cfg_scale,
            "sound": self.sound,
            "duration": self.duration,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/kwaivgi/kling-v2.6-pro/text-to-video"

    def field_order(self):
        return [
            "prompt",
            "negative_prompt",
            "aspect_ratio",
            "cfg_scale",
            "sound",
            "duration",
        ]
