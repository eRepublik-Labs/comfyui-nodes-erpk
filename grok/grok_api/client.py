# ABOUTME: GrokClient — async public surface over the native xai-sdk for ComfyUI parallelism.
# ABOUTME: Sync bodies in _<name>_sync helpers wrapped via asyncio.to_thread (Wavespeed pattern).

import asyncio
import configparser
import os
from typing import Any, Dict, List, Optional


class GrokClient:
    """Client for xAI's Grok API, covering text, image, and video capabilities.

    Public methods are async so ComfyUI's executor can interleave concurrent
    Grok nodes. The sync xai-sdk calls happen inside asyncio.to_thread, which
    preserves the SDK's internal retry / polling behavior while releasing the
    event loop during the wait.

    Multi-tier API key resolution: explicit arg > ComfyUI Settings >
    config.ini.
    """

    DEFAULT_TEXT_MODEL = "grok-4.7"
    DEFAULT_IMAGE_MODEL = "grok-imagine-image-2.0"
    DEFAULT_VIDEO_MODEL = "grok-imagine-video"
    VIDEO_MODELS = ["grok-imagine-video", "grok-imagine-video-1.5"]
    # Video edit and extend take a source video; grok-imagine-video-1.5 has no
    # video input (docs.x.ai model page and /v1/video-generation-models).
    VIDEO_INPUT_MODELS = ["grok-imagine-video"]

    # Current Grok image model per docs.x.ai. grok-imagine-image (v1) and
    # grok-imagine-image-quality were dropped on 2026-10-01; -quality retires on
    # 2026-11-02 and redirects to 2.0 with quality=low.
    IMAGE_MODELS = ["grok-imagine-image-2.0"]

    # Retired-ID remaps applied at execute time. Empty today; kept so a future
    # retired ID can map to its canonical successor while staying selectable in
    # saved workflows (ComfyUI validates Combo values before execute).
    IMAGE_MODEL_ALIASES = {}
    # Every ratio the xai-sdk ImageAspectRatio literal can express, plus "auto"
    # (sent as unset). New values are appended so saved workflows keep theirs.
    # 21:9 and 5:2 exist for 2.0 on REST only (no SDK literal or proto enum).
    IMAGE_ASPECT_RATIOS = [
        "1:1", "16:9", "9:16", "4:3", "3:4", "2:1", "1:2", "auto",
        "3:2", "2:3", "19.5:9", "9:19.5", "20:9", "9:20",
    ]
    # SDK ImageQuality literal is low/medium; "auto" leaves the field unset.
    IMAGE_QUALITIES = ["auto", "low", "medium"]
    MAX_IMAGES_PER_REQUEST = 10  # n range 1-10 per docs.x.ai images/generation
    IMAGE_RESOLUTIONS = ["1k", "2k"]

    VIDEO_ASPECT_RATIOS = ["16:9", "9:16", "1:1", "4:3", "3:4", "3:2", "2:3"]
    VIDEO_RESOLUTIONS = ["480p", "720p"]

    MAX_EDIT_IMAGES = 5  # grok-imagine-image-2.0 multi-image edit cap (docs.x.ai)
    MAX_REFERENCE_IMAGES = 3  # reference-to-video images we send (API max undocumented)

    # reasoning_effort per model, from live gRPC probes on xai-sdk 1.20
    # (2026-10-01). grok-4.7 accepts low..xhigh and returns 400 on "none".
    # grok-4.20-0309-non-reasoning, grok-4.20-multi-agent-0309 and
    # grok-build-0.1 return 400 "does not support parameter reasoningEffort",
    # so any model missing from this dict never receives the field.
    REASONING_EFFORTS_BY_MODEL = {
        "grok-4.7": ["low", "medium", "high", "xhigh"],
    }
    REASONING_EFFORT_OPTIONS = ["(model default)", "none", "low", "medium", "high", "xhigh"]
    REASONING_EFFORT_MODEL_DEFAULT = "(model default)"

    def __init__(self, api_key: Optional[str] = None, config_path: Optional[str] = None):
        self.api_key = self._resolve_api_key(api_key, config_path)
        # Lazily import to avoid crashing tests when xai-sdk isn't installed.
        try:
            import xai_sdk
        except ImportError:
            xai_sdk = None
        self._xai_sdk = xai_sdk
        self._client = None

    def _resolve_api_key(self, api_key: Optional[str], config_path: Optional[str]) -> str:
        """Priority: ComfyUI Settings > arg > config.ini."""
        try:
            from ...settings import get_comfy_setting
            settings_key = get_comfy_setting("ERPK.XAI_API_KEY")
            if settings_key:
                print("[Grok] Using API key from ComfyUI Settings")
                return settings_key
        except (ImportError, ValueError):
            pass

        if api_key and api_key.strip():
            print("[Grok] Using API key from node input")
            return api_key.strip()

        if config_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(os.path.dirname(current_dir), "config.ini")

        try:
            cfg = configparser.ConfigParser()
            cfg.read(config_path)
            file_key = cfg["API"]["XAI_API_KEY"].strip()
            if file_key:
                print("[Grok] Using API key from config.ini")
                return file_key
        except (KeyError, configparser.Error):
            pass

        raise ValueError(
            "No xAI API key found. Provide via:\n"
            "  1. ComfyUI Settings (Settings > ERPK > API Keys > xAI)\n"
            "  2. The api_key input on the Grok API Client node\n"
            "  3. grok/config.ini"
        )

    def _ensure_client(self):
        if self._client is not None:
            return self._client
        if self._xai_sdk is None:
            raise ImportError(
                "xai-sdk is required. Install with: pip install xai-sdk>=1.20.0"
            )
        self._client = self._xai_sdk.Client(api_key=self.api_key, timeout=3600)
        return self._client

    # ------------------------------------------------------------------
    # Text generation
    # ------------------------------------------------------------------

    @classmethod
    def resolve_reasoning_effort(cls, model: str, effort: Optional[str]) -> Optional[str]:
        """Return the reasoning_effort to send for `model`, or None to omit it.

        Omitted for "(model default)" and for models that reject the field.
        A value the model rejects is clamped to its lowest accepted effort
        (grok-4.7 + "none" -> "low").
        """
        accepted = cls.REASONING_EFFORTS_BY_MODEL.get(model)
        if not accepted or not effort or effort == cls.REASONING_EFFORT_MODEL_DEFAULT:
            return None
        return effort if effort in accepted else accepted[0]

    def _generate_text_sync(
        self,
        messages: List[Dict[str, str]],
        model: str = DEFAULT_TEXT_MODEL,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """One-shot chat completion. Returns {'text', 'model', 'response_id', 'usage'}."""
        client = self._ensure_client()
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        chat = client.chat.create(model=model, temperature=temperature, **kwargs)
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                chat.append(self._xai_sdk.chat.system(content))
            elif role == "assistant":
                chat.append(self._xai_sdk.chat.assistant(content))
            else:
                chat.append(self._xai_sdk.chat.user(content))
        response = chat.sample()
        return {
            "text": getattr(response, "content", str(response)),
            "model": model,
            "response_id": getattr(response, "id", None),
            "usage": getattr(response, "usage", None),
        }

    async def generate_text(
        self,
        messages: List[Dict[str, str]],
        model: str = DEFAULT_TEXT_MODEL,
        **kwargs,
    ) -> Dict[str, Any]:
        return await asyncio.to_thread(self._generate_text_sync, messages, model, **kwargs)

    def _continue_response_sync(
        self,
        previous_response_id: str,
        messages: List[Dict[str, str]],
        model: str = DEFAULT_TEXT_MODEL,
        **kwargs,
    ) -> Dict[str, Any]:
        """Stateful continuation via the Responses API (previous_response_id chaining)."""
        client = self._ensure_client()
        response = client.responses.create(
            model=model,
            input=messages,
            previous_response_id=previous_response_id,
            **kwargs,
        )
        return {
            "text": getattr(response, "output_text", str(response)),
            "model": model,
            "response_id": getattr(response, "id", None),
        }

    async def continue_response(
        self,
        previous_response_id: str,
        messages: List[Dict[str, str]],
        model: str = DEFAULT_TEXT_MODEL,
        **kwargs,
    ) -> Dict[str, Any]:
        return await asyncio.to_thread(
            self._continue_response_sync, previous_response_id, messages, model, **kwargs
        )

    # ------------------------------------------------------------------
    # Image generation / editing
    # ------------------------------------------------------------------

    def _resolve_image_model(self, model: str) -> str:
        """Translate deprecated model aliases to the SDK's canonical IDs."""
        return self.IMAGE_MODEL_ALIASES.get(model, model)

    @staticmethod
    def _image_request_kwargs(
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        quality: Optional[str] = None,
    ) -> Dict[str, Any]:
        """SDK kwargs for image.sample / sample_batch.

        "auto" has no SDK literal for aspect_ratio, resolution or quality
        (xai_sdk raises ValueError on it), so it is omitted and the API applies
        its default.
        """
        kwargs: Dict[str, Any] = {}
        if aspect_ratio and aspect_ratio != "auto":
            kwargs["aspect_ratio"] = aspect_ratio
        if resolution and resolution != "auto":
            kwargs["resolution"] = resolution
        if quality and quality != "auto":
            kwargs["quality"] = quality
        return kwargs

    def _generate_image_sync(
        self,
        prompt: str,
        model: str = DEFAULT_IMAGE_MODEL,
        aspect_ratio: str = "1:1",
        resolution: str = "1k",
        n: int = 1,
        quality: Optional[str] = None,
        **kwargs,
    ) -> List[str]:
        """Returns a list of image URLs (length n)."""
        client = self._ensure_client()
        model = self._resolve_image_model(model)
        call_kwargs = self._image_request_kwargs(
            aspect_ratio=aspect_ratio, resolution=resolution, quality=quality
        )
        call_kwargs.update(kwargs)
        if n <= 1:
            response = client.image.sample(prompt, model, **call_kwargs)
            return [response.url] if getattr(response, "url", None) else []
        # n > 1 uses the batch endpoint; returns a sequence of ImageResponse.
        responses = client.image.sample_batch(prompt, model, n, **call_kwargs)
        return [r.url for r in responses if getattr(r, "url", None)]

    async def generate_image(self, prompt: str, **kwargs) -> List[str]:
        return await asyncio.to_thread(self._generate_image_sync, prompt, **kwargs)

    def _edit_image_sync(
        self,
        prompt: str,
        image_urls: List[str],
        model: str = DEFAULT_IMAGE_MODEL,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        quality: Optional[str] = None,
        n: int = 1,
        **kwargs,
    ) -> List[str]:
        """Edit one or more source images; returns a list of image URLs (length n).

        SDK takes `image_url` (singular) for one source and `image_urls` (plural)
        for multi-image edit — mutually exclusive. Cap: MAX_EDIT_IMAGES sources."""
        if not image_urls:
            raise ValueError("edit_image requires at least one source image URL or data URI")
        client = self._ensure_client()
        model = self._resolve_image_model(model)
        call_kwargs: Dict[str, Any] = {}
        if len(image_urls) == 1:
            call_kwargs["image_url"] = image_urls[0]
        else:
            call_kwargs["image_urls"] = image_urls[: self.MAX_EDIT_IMAGES]
        call_kwargs.update(self._image_request_kwargs(
            aspect_ratio=aspect_ratio, resolution=resolution, quality=quality
        ))
        call_kwargs.update(kwargs)
        if n <= 1:
            response = client.image.sample(prompt, model, **call_kwargs)
            return [response.url] if getattr(response, "url", None) else []
        responses = client.image.sample_batch(prompt, model, n, **call_kwargs)
        return [r.url for r in responses if getattr(r, "url", None)]

    async def edit_image(self, prompt: str, image_urls: List[str], **kwargs) -> List[str]:
        return await asyncio.to_thread(self._edit_image_sync, prompt, image_urls, **kwargs)

    # ------------------------------------------------------------------
    # Video generation / editing / extension
    # ------------------------------------------------------------------

    def _generate_video_sync(
        self,
        prompt: str,
        model: str = DEFAULT_VIDEO_MODEL,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
        reference_images: Optional[List[str]] = None,
        video_url: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Returns the output video URL. xai-sdk blocks internally until done.

        Modes (mutually exclusive after prompt):
        - text-to-video: just prompt
        - reference-to-video: prompt + reference_images (SDK kwarg: reference_image_urls)
        - video-edit: prompt + video_url
        """
        client = self._ensure_client()
        call_kwargs: Dict[str, Any] = {
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
        }
        if reference_images:
            call_kwargs["reference_image_urls"] = reference_images
        if video_url:
            call_kwargs["video_url"] = video_url
        call_kwargs.update(kwargs)
        response = client.video.generate(prompt, model, **call_kwargs)
        return getattr(response, "url", "")

    async def generate_video(self, prompt: str, **kwargs) -> str:
        return await asyncio.to_thread(self._generate_video_sync, prompt, **kwargs)

    def _edit_video_sync(
        self,
        prompt: str,
        video_url: str,
        model: str = DEFAULT_VIDEO_MODEL,
        **kwargs,
    ) -> str:
        """Edit-mode variant of generate_video. Output inherits source's
        duration/aspect/resolution (capped at 720p per xAI docs)."""
        if not video_url:
            raise ValueError("edit_video requires a source video URL")
        return self._generate_video_sync(prompt=prompt, video_url=video_url, model=model, **kwargs)

    async def edit_video(self, prompt: str, video_url: str, **kwargs) -> str:
        return await asyncio.to_thread(self._edit_video_sync, prompt, video_url, **kwargs)

    def _extend_video_sync(
        self,
        video_url: str,
        duration: int = 5,
        prompt: Optional[str] = None,
        model: str = DEFAULT_VIDEO_MODEL,
        **kwargs,
    ) -> str:
        """Append `duration` seconds of new content to the input video.

        SDK signature: extend(prompt, model, video_url, *, duration, ...).
        `prompt` is positional and non-Optional; pass empty string when the
        node's caller didn't supply one.
        """
        if not video_url:
            raise ValueError("extend_video requires a source video URL")
        client = self._ensure_client()
        response = client.video.extend(
            prompt or "",
            model,
            video_url,
            duration=duration,
            **kwargs,
        )
        return getattr(response, "url", "")

    async def extend_video(self, video_url: str, duration: int = 5, **kwargs) -> str:
        return await asyncio.to_thread(self._extend_video_sync, video_url, duration, **kwargs)
