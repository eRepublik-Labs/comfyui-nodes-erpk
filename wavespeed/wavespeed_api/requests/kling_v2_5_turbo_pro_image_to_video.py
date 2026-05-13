# ABOUTME: Kling 2.5 Turbo Pro image-to-video request for WaveSpeed AI.
# ABOUTME: Routes to the kling-v2.5-turbo-pro image-to-video endpoint and adds a last_image keyframe.

from typing import Optional
from pydantic import Field
from .kling_v2_5_turbo_std_image_to_video import KlingV2_5TurboStdImageToVideo


class KlingV2_5TurboProImageToVideo(KlingV2_5TurboStdImageToVideo):
    """
    Kling 2.5 Turbo Pro image-to-video model.

    Same parameters as the Std variant plus an optional `last_image` end-frame
    for keyframe interpolation, and routed to the Pro endpoint.
    """

    last_image: Optional[str] = Field(
        default="",
        description="Optional end-frame URL for keyframe interpolation.",
    )

    def build_payload(self) -> dict:
        payload = {
            "prompt": self.prompt,
            "image": self.image,
            "last_image": self.last_image,
            "negative_prompt": self.negative_prompt,
            "guidance_scale": self.guidance_scale,
            "duration": self.duration,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        return "/api/v3/kwaivgi/kling-v2.5-turbo-pro/image-to-video"

    def field_order(self):
        return [
            "prompt",
            "image",
            "last_image",
            "negative_prompt",
            "guidance_scale",
            "duration",
        ]
