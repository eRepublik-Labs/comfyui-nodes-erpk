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
    XAI_API_KEY env var > config.ini.
    """

    DEFAULT_TEXT_MODEL = "grok-4.3"
    DEFAULT_IMAGE_MODEL = "grok-imagine-image-quality"
    DEFAULT_VIDEO_MODEL = "grok-imagine-video"

    IMAGE_MODELS = [
        "grok-imagine-image-quality",
    ]
    IMAGE_ASPECT_RATIOS = ["1:1", "16:9", "9:16", "4:3", "3:4", "2:1", "1:2", "auto"]
    IMAGE_RESOLUTIONS = ["1k", "2k"]

    VIDEO_ASPECT_RATIOS = ["16:9", "9:16", "1:1", "4:3", "3:4", "3:2", "2:3"]
    VIDEO_RESOLUTIONS = ["480p", "720p"]

    MAX_EDIT_IMAGES = 3  # xAI multi-image edit cap per docs

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
        """Priority: ComfyUI Settings > arg > XAI_API_KEY env > config.ini."""
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

        env_key = os.getenv("XAI_API_KEY", "").strip()
        if env_key:
            print("[Grok] Using API key from environment variable XAI_API_KEY")
            return env_key

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
            "  3. XAI_API_KEY environment variable\n"
            "  4. grok/config.ini"
        )

    def _ensure_client(self):
        if self._client is not None:
            return self._client
        if self._xai_sdk is None:
            raise ImportError(
                "xai-sdk is required. Install with: pip install xai-sdk>=1.14.0"
            )
        self._client = self._xai_sdk.Client(api_key=self.api_key, timeout=3600)
        return self._client

    # ------------------------------------------------------------------
    # Text generation
    # ------------------------------------------------------------------

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

    def _generate_image_sync(
        self,
        prompt: str,
        model: str = DEFAULT_IMAGE_MODEL,
        aspect_ratio: str = "1:1",
        resolution: str = "1k",
        n: int = 1,
        **kwargs,
    ) -> List[str]:
        """Returns a list of image URLs (length n)."""
        client = self._ensure_client()
        response = client.image.sample(
            prompt=prompt,
            model=model,
            n=n,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            **kwargs,
        )
        # The xai-sdk returns either a single response or a batch object.
        urls: List[str] = []
        if hasattr(response, "url") and response.url:
            urls.append(response.url)
        if hasattr(response, "images"):
            for item in response.images:
                if hasattr(item, "url") and item.url:
                    urls.append(item.url)
        return urls

    async def generate_image(self, prompt: str, **kwargs) -> List[str]:
        return await asyncio.to_thread(self._generate_image_sync, prompt, **kwargs)

    def _edit_image_sync(
        self,
        prompt: str,
        image_urls: List[str],
        model: str = DEFAULT_IMAGE_MODEL,
        aspect_ratio: Optional[str] = None,
        **kwargs,
    ) -> List[str]:
        """Edit one or more source images (URL or data URI). Cap: 3 images."""
        if not image_urls:
            raise ValueError("edit_image requires at least one source image URL or data URI")
        client = self._ensure_client()
        image_arg = image_urls[0] if len(image_urls) == 1 else image_urls[: self.MAX_EDIT_IMAGES]
        call_kwargs: Dict[str, Any] = {
            "prompt": prompt,
            "model": model,
            "image_url": image_arg,
        }
        if aspect_ratio:
            call_kwargs["aspect_ratio"] = aspect_ratio
        call_kwargs.update(kwargs)
        response = client.image.sample(**call_kwargs)
        urls: List[str] = []
        if hasattr(response, "url") and response.url:
            urls.append(response.url)
        if hasattr(response, "images"):
            for item in response.images:
                if hasattr(item, "url") and item.url:
                    urls.append(item.url)
        return urls

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
        - reference-to-video: prompt + reference_images
        - video-edit: prompt + video_url
        """
        client = self._ensure_client()
        call_kwargs: Dict[str, Any] = {
            "prompt": prompt,
            "model": model,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
        }
        if reference_images:
            call_kwargs["reference_images"] = reference_images
        if video_url:
            call_kwargs["video_url"] = video_url
        call_kwargs.update(kwargs)
        response = client.video.generate(**call_kwargs)
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

        Uses /v1/videos/extensions. The xai-sdk exposes this via
        `client.video.extend(...)` — falls back to a direct extensions call
        if the SDK method signature differs.
        """
        if not video_url:
            raise ValueError("extend_video requires a source video URL")
        client = self._ensure_client()
        call_kwargs: Dict[str, Any] = {
            "video_url": video_url,
            "duration": duration,
            "model": model,
        }
        if prompt:
            call_kwargs["prompt"] = prompt
        call_kwargs.update(kwargs)
        if hasattr(client.video, "extend"):
            response = client.video.extend(**call_kwargs)
        else:
            # SDK doesn't expose extend yet; pass mode through generate.
            response = client.video.generate(mode="extend-video", **call_kwargs)
        return getattr(response, "url", "")

    async def extend_video(self, video_url: str, duration: int = 5, **kwargs) -> str:
        return await asyncio.to_thread(self._extend_video_sync, video_url, duration, **kwargs)
