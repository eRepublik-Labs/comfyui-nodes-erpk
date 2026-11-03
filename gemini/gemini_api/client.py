# ABOUTME: Google Gemini API client using the new google-genai SDK
# ABOUTME: Handles authentication, requests, and error handling

import asyncio
import os
import configparser
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types

from .cooperative_call import call_with_retry, resolve_timeout_ms

# Minimum recommended SDK version
MIN_SDK_VERSION = "1.56.0"
_sdk_version_checked = False


def _check_sdk_version():
    """Warn once if google-genai SDK is outdated."""
    global _sdk_version_checked
    if _sdk_version_checked:
        return
    _sdk_version_checked = True

    try:
        from packaging import version
        current = getattr(genai, "__version__", "0.0.0")
        if version.parse(current) < version.parse(MIN_SDK_VERSION):
            print(f"[Gemini] Warning: google-genai {current} is outdated. "
                  f"Recommended: >={MIN_SDK_VERSION}. Run: pip install --upgrade google-genai")
    except ImportError:
        pass  # packaging not available, skip check


def stop_reason(response) -> Optional[str]:
    """Why Gemini stopped, as an enum name such as "STOP" or "MAX_TOKENS".

    The first candidate's finish reason, or the prompt's block reason when no
    candidate came back. None when the response reports neither.
    """
    if response.candidates:
        reason = response.candidates[0].finish_reason
    else:
        reason = getattr(getattr(response, "prompt_feedback", None), "block_reason", None)
    return None if reason is None else str(reason).split(".")[-1].upper()


def raise_if_cut_off(response, max_tokens: int) -> None:
    """Refuse a reply that stopped at max_output_tokens: its text is cut off,
    or absent when thinking used the whole budget."""
    if stop_reason(response) == "MAX_TOKENS":
        raise ValueError(
            f"Gemini's reply was cut off at max_output_tokens={max_tokens} "
            "(thinking counts toward it); raise max_output_tokens"
        )


class GeminiClient:
    """
    Client for interacting with Google Gemini API using google-genai SDK.

    Features:
    - Multi-source API key management (input → env → config)
    - All Gemini models support
    - Text generation and vision capabilities
    - Safety settings configuration
    - System instructions support
    """

    # Available models
    MODELS = {
        "gemini-4-argon": "Gemini 4 Argon (Flagship reasoning; low/medium/high thinking; ignores temperature/top_p/top_k)",
        "gemini-3.1-pro-preview": "Gemini 3.1 Pro Preview (Most advanced reasoning)",
        "gemini-3.8-flash": "Gemini 3.8 Flash (Latest Flash; no minimal thinking)",
        "gemini-3.7-flash": "Gemini 3.7 Flash (Deprecated 2026-10-08; served by 3.8 Flash)",
        "gemini-3.6-flash": "Gemini 3.6 Flash (Improved token efficiency, cheaper than 3.5 Flash)",
        "gemini-3.5-flash": "Gemini 3.5 Flash (Deprecated 2026-10-08; served by 3.6 Flash)",
        "gemini-3.5-flash-lite": "Gemini 3.5 Flash-Lite (Fastest, most cost-effective 3.5 model)",
    }

    # Image generation models
    IMAGE_MODELS = [
        "gemini-nano-banana-2.1",
        "gemini-3.1-flash-image",
        "gemini-3.1-flash-lite-image",
        "gemini-3-pro-image",
    ]

    # Default configuration
    DEFAULT_MODEL = "gemini-3.8-flash"
    DEFAULT_IMAGE_MODEL = "gemini-nano-banana-2.1"
    DEFAULT_MAX_TOKENS = 8192
    DEFAULT_TEMPERATURE = 0.7

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        config_path: Optional[str] = None
    ):
        """
        Initialize Gemini API client.

        Args:
            api_key: Google API key (optional, will check env/config)
            model: Gemini model to use
            config_path: Path to config.ini file
        """
        # Check SDK version on first client creation
        _check_sdk_version()

        self.model_name = model

        # Resolve API key from multiple sources
        self.api_key = self._resolve_api_key(api_key, config_path)

        # Initialize the client with a bounded HTTP timeout so stuck calls
        # surface as errors instead of hanging the ComfyUI executor. The SDK
        # applies this to every HTTP request; AFC rounds each get their own
        # timeout, so worst-case wall time is roughly N_AFC × timeout.
        # Tunable via the ERPK.GEMINI_TIMEOUT_MS setting (resolve_timeout_ms).
        http_options = types.HttpOptions(timeout=resolve_timeout_ms())
        self.client = genai.Client(api_key=self.api_key, http_options=http_options)

        # Store configuration for later use
        self.system_instruction = None
        self.safety_settings = None

    def _resolve_api_key(self, api_key: Optional[str], config_path: Optional[str]) -> str:
        """
        Resolve API key from multiple sources in order of priority:
        1. ComfyUI Settings (comfy.settings.json)
        2. Provided api_key parameter
        3. config.ini file

        Args:
            api_key: API key provided directly
            config_path: Path to config.ini

        Returns:
            Resolved API key

        Raises:
            ValueError: If no API key found
        """
        # Priority 1: ComfyUI Settings
        try:
            from ...settings import get_comfy_setting
            settings_key = get_comfy_setting("ERPK.GOOGLE_API_KEY")
            if settings_key:
                return settings_key
        except (ImportError, ValueError):
            pass

        # Priority 2: Direct parameter
        if api_key and api_key.strip():
            return api_key.strip()

        # Priority 3: Config file
        if config_path is None:
            # Default to config.ini in same directory as this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(os.path.dirname(current_dir), "config.ini")

        if os.path.exists(config_path):
            config = configparser.ConfigParser()
            config.read(config_path)
            if "gemini" in config and "api_key" in config["gemini"]:
                return config["gemini"]["api_key"]

        raise ValueError(
            "No API key found. Please provide via:\\n"
            "1. ComfyUI Settings (Settings > ERPK > API Keys)\\n"
            "2. api_key parameter\\n"
            "3. config.ini file in gemini/ directory"
        )

    def update_config(
        self,
        system_instruction: Optional[str] = None,
        safety_settings: Optional[Dict] = None
    ):
        """
        Update client configuration.

        Args:
            system_instruction: System-level instruction for the model
            safety_settings: Safety settings configuration
        """
        if system_instruction:
            self.system_instruction = system_instruction
        if safety_settings:
            self.safety_settings = safety_settings

    def request_config(self, **params) -> types.GenerateContentConfig:
        """Build a request config that carries this client's system instruction
        and safety settings.

        Every request needs both on its own config: a chat's per-message config
        replaces the session config rather than merging with it (google-genai
        chats.py, send_message), so settings given only to start_chat are lost.
        """
        config = types.GenerateContentConfig(**params)
        if self.system_instruction:
            config.system_instruction = self.system_instruction
        if self.safety_settings:
            config.safety_settings = self.safety_settings
        return config

    @staticmethod
    def _normalize_usage(usage_metadata):
        """Read the SDK's usage_metadata into {input_tokens, output_tokens, total_tokens}.

        output_tokens is candidates_token_count plus thoughts_token_count.
        candidates_token_count excludes thinking (measured 2026-11-03: on 55 of
        55 replies that thought, total = prompt + candidates + thoughts), and
        Google bills thinking tokens at the output rate. Returns None when no
        usage is reported. Each field is coerced defensively so a missing or
        non-int count reads 0.
        """
        if usage_metadata is None:
            return None

        def _count(name):
            value = getattr(usage_metadata, name, None)
            return value if isinstance(value, int) else 0

        input_tokens = _count("prompt_token_count")
        output_tokens = _count("candidates_token_count") + _count("thoughts_token_count")
        total = getattr(usage_metadata, "total_token_count", None)
        total_tokens = total if isinstance(total, int) else input_tokens + output_tokens
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
        }

    def _generate_content_sync(
        self,
        prompt: str,
        images: Optional[List[Any]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        response_mime_type: Optional[str] = None,
        response_schema: Optional[Dict] = None,
        thinking_config: Optional[Any] = None,
        seed: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS
        temperature = temperature if temperature is not None else self.DEFAULT_TEMPERATURE
        model_to_use = model or self.model_name

        # Build generation config
        config_params = {
            "max_output_tokens": max_tokens,
            "temperature": temperature,
        }

        # Add optional sampling parameters
        if top_p is not None:
            config_params["top_p"] = top_p
        if top_k is not None:
            config_params["top_k"] = top_k
        if stop_sequences is not None:
            config_params["stop_sequences"] = stop_sequences

        # Add JSON mode parameters
        if response_mime_type is not None:
            config_params["response_mime_type"] = response_mime_type
        if response_schema is not None:
            config_params["response_schema"] = response_schema

        if seed is not None:
            config_params["seed"] = seed

        # Per-request timeout: the genai.Client one is fixed at construction,
        # and some models (Gemini 4 Argon) need longer than the default.
        timeout_ms = resolve_timeout_ms(model_to_use)
        config_params["http_options"] = types.HttpOptions(timeout=timeout_ms)

        config = self.request_config(**config_params)

        # Add thinking config if provided
        if thinking_config is not None:
            config.thinking_config = thinking_config

        # Build content list (images + text)
        contents = []
        if images:
            contents.extend(images)
        contents.append(prompt)

        # Generate content via the cooperative-call helper so ComfyUI's
        # /interrupt button can abort an in-flight call. Transient server
        # errors get exponential-backoff retries.
        response = call_with_retry(
            self.client.models.generate_content,
            model=model_to_use,
            contents=contents,
            config=config,
            timeout_s=timeout_ms / 1000.0,
        )

        # Extract text from response
        usage = self._normalize_usage(getattr(response, "usage_metadata", None))
        raise_if_cut_off(response, max_tokens)
        finish_reason = stop_reason(response)
        try:
            text = response.text
        except Exception as e:
            # Response was blocked or error occurred
            return {
                "text": "",
                "blocked": True,
                "finish_reason": finish_reason or "ERROR",
                "error": str(e),
                "usage": usage
            }
        # The SDK returns None rather than raising when the prompt was blocked
        # or the candidate came back with no text parts (a SAFETY stop).
        if text is None:
            return {
                "text": "",
                "blocked": True,
                "finish_reason": finish_reason or "ERROR",
                "error": f"Gemini returned no text (reason: {finish_reason})",
                "usage": usage
            }
        return {
            "text": text,
            "blocked": False,
            "finish_reason": finish_reason or "STOP",
            "usage": usage
        }

    async def generate_content(
        self,
        prompt: str,
        images: Optional[List[Any]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        response_mime_type: Optional[str] = None,
        response_schema: Optional[Dict] = None,
        thinking_config: Optional[Any] = None,
        seed: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate content using Gemini API.

        Runs in a worker thread via asyncio.to_thread so the event loop is free
        for other parallel API nodes while the SDK call (and its retry/interrupt
        polling loop) is in progress.

        Args:
            prompt: Text prompt
            images: Optional list of PIL Images for vision tasks
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            model: Optional model override (uses client default if not specified)
            top_p: Nucleus sampling threshold (None to disable)
            top_k: Top-k sampling limit (None to disable)
            stop_sequences: List of sequences where generation stops
            response_mime_type: Output format (e.g., "application/json")
            response_schema: JSON schema dict for structured output
            **kwargs: Additional parameters

        Returns:
            Response dict with 'text' and metadata
        """
        return await asyncio.to_thread(
            self._generate_content_sync,
            prompt,
            images=images,
            max_tokens=max_tokens,
            temperature=temperature,
            model=model,
            top_p=top_p,
            top_k=top_k,
            stop_sequences=stop_sequences,
            response_mime_type=response_mime_type,
            response_schema=response_schema,
            thinking_config=thinking_config,
            seed=seed,
            **kwargs,
        )

    def start_chat(self, model: Optional[str] = None, history: Optional[List[Dict[str, str]]] = None, thinking_config: Optional[Any] = None):
        """
        Start a chat session for multi-turn conversations.

        Args:
            model: Optional model to use (uses client default if not specified)
            history: Optional chat history

        Returns:
            Chat session object
        """
        model_to_use = model or self.model_name

        # Build config
        config = self.request_config()
        if thinking_config is not None:
            config.thinking_config = thinking_config

        # Create chat
        return self.client.chats.create(
            model=model_to_use,
            config=config
        )
