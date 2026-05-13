# ABOUTME: Google Gemini API client using the new google-genai SDK
# ABOUTME: Handles authentication, requests, and error handling

import os
import configparser
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types

from .cooperative_call import call_with_retry

# Minimum recommended SDK version
MIN_SDK_VERSION = "1.56.0"
_sdk_version_checked = False

# Per-request HTTP timeout for the google-genai SDK. Without this, a stuck call
# can hang the ComfyUI executor indefinitely (observed: 42-minute ghost jobs on
# image-edit calls). Override via ERPK_GEMINI_TIMEOUT_MS env var. The SDK applies
# this timeout to every HTTP request made by the client; AFC rounds each get
# their own timeout, so the worst-case wall time is roughly N_AFC × timeout.
DEFAULT_HTTP_TIMEOUT_MS = int(os.environ.get("ERPK_GEMINI_TIMEOUT_MS", "300000"))


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
        "gemini-3.1-pro-preview": "Gemini 3.1 Pro Preview (Most advanced reasoning)",
        "gemini-3-pro-preview": "Gemini 3 Pro Preview (Most intelligent, best reasoning)",
        "gemini-3-flash-preview": "Gemini 3 Flash Preview (Balanced speed and intelligence)",
        "gemini-3.1-flash-lite-preview": "Gemini 3.1 Flash-Lite Preview (Fastest, most cost-efficient)",
        "gemini-2.5-pro": "Gemini 2.5 Pro (Complex reasoning, 1M context)",
        "gemini-2.5-flash": "Gemini 2.5 Flash (Best price-performance)",
        "gemini-2.5-flash-lite": "Gemini 2.5 Flash-Lite (Fastest, most cost-efficient)",
    }

    # Image generation models
    IMAGE_MODELS = [
        "gemini-3.1-flash-image-preview",
        "gemini-3-pro-image-preview",
        "gemini-2.5-flash-image",
    ]

    # Default configuration
    DEFAULT_MODEL = "gemini-3-flash-preview"
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
        # surface as errors instead of hanging the ComfyUI executor.
        http_options = types.HttpOptions(timeout=DEFAULT_HTTP_TIMEOUT_MS)
        self.client = genai.Client(api_key=self.api_key, http_options=http_options)

        # Store configuration for later use
        self.system_instruction = None
        self.safety_settings = None

    def _resolve_api_key(self, api_key: Optional[str], config_path: Optional[str]) -> str:
        """
        Resolve API key from multiple sources in order of priority:
        1. ComfyUI Settings (comfy.settings.json)
        2. Provided api_key parameter
        3. GOOGLE_API_KEY or GEMINI_API_KEY environment variable
        4. config.ini file

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

        # Priority 2: Environment variable
        env_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if env_key:
            return env_key

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
            "3. GOOGLE_API_KEY or GEMINI_API_KEY environment variable\\n"
            "4. config.ini file in gemini/ directory"
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

    def generate_content(
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

        config = types.GenerateContentConfig(**config_params)

        # Add system instruction if set
        if self.system_instruction:
            config.system_instruction = self.system_instruction

        # Add safety settings if set
        if self.safety_settings:
            config.safety_settings = self.safety_settings

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
        )

        # Extract text from response
        try:
            text = response.text
            return {
                "text": text,
                "blocked": False,
                "finish_reason": response.candidates[0].finish_reason if response.candidates else "STOP"
            }
        except Exception as e:
            # Response was blocked or error occurred
            return {
                "text": "",
                "blocked": True,
                "finish_reason": response.candidates[0].finish_reason if response.candidates else "ERROR",
                "error": str(e)
            }

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
        config = types.GenerateContentConfig()
        if self.system_instruction:
            config.system_instruction = self.system_instruction
        if self.safety_settings:
            config.safety_settings = self.safety_settings
        if thinking_config is not None:
            config.thinking_config = thinking_config

        # Create chat
        return self.client.chats.create(
            model=model_to_use,
            config=config
        )
