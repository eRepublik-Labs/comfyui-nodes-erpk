# ABOUTME: MiniMax H3 video-edit request for WaveSpeed AI.
# ABOUTME: Routes to the wavespeed-ai/minimax-h3 video-edit endpoint.

from typing import List, Optional
from pydantic import Field
from ..utils import BaseRequest


class MinimaxH3VideoEdit(BaseRequest):
    """
    MiniMax H3 video-edit model.

    Rewrites lighting, style, environment or specific elements of an input
    video while the video itself drives identity, composition and motion.
    Unset duration and aspect ratio follow the input. Billing counts input
    plus output seconds, each capped at 15. No LoRA twin exists.
    """

    prompt: str = Field(..., description="Describes the edit; references cited as <Picture N> and <Audio N>.")
    video: str = Field(..., description="URL of the input video to edit.")
    reference_images: Optional[List[str]] = Field(default=None, description="Reference image URLs (0-9).", max_length=9)
    reference_audios: Optional[List[str]] = Field(default=None, description="Reference audio URLs (0-3).", max_length=3)
    resolution: Optional[str] = Field(default="480p", description="Output resolution: 480p, 540p, 768p or 1080p.")
    aspect_ratio: Optional[str] = Field(default=None, description="Output aspect ratio; unset adapts to the input video.")
    duration: Optional[int] = Field(default=None, description="Output duration in seconds; unset matches the input.", ge=3, le=15)
    generate_audio: Optional[bool] = Field(default=True, description="False preserves the input's audio track instead of generating one.")
    seed: Optional[int] = Field(default=-1, description="Random seed; a negative value generates a random seed.", ge=-1, le=2147483647)

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = {
            "prompt": self.prompt,
            "video": self.video,
            "reference_images": self.reference_images,
            "reference_audios": self.reference_audios,
            "resolution": self.resolution,
            "aspect_ratio": self.aspect_ratio,
            "duration": self.duration,
            "generate_audio": self.generate_audio,
            "seed": self.seed,
        }
        return self._remove_empty_fields(payload)

    def get_api_path(self):
        """Gets the API path. Corresponds to api_path in the JSON."""
        return "/api/v3/wavespeed-ai/minimax-h3/video-edit"

    def field_required(self):
        return ["prompt", "video"]

    def field_order(self):
        return ["prompt", "video", "reference_images", "reference_audios", "resolution",
                "aspect_ratio", "duration", "generate_audio", "seed"]
