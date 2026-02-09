# ABOUTME: OpenAI API client using the official openai SDK
# ABOUTME: Handles authentication, chat completions, and image generation

import os
import configparser
import time
from typing import Dict, Any, List, Optional


class OpenAIClient:
    """
    Client for interacting with OpenAI API.

    Features:
    - Multi-source API key management (input -> env -> config)
    - All GPT models support
    - Text generation and vision capabilities
    - Image generation with DALL-E and GPT-Image models
    """

    # Available text/vision models
    MODELS = {
        "gpt-5.2": "GPT-5.2 (Latest flagship, best for coding/agents)",
        "gpt-5.2-pro": "GPT-5.2 Pro (Smarter, more precise responses)",
        "gpt-5.1": "GPT-5.1 (Coding/agents with configurable reasoning)",
        "gpt-5": "GPT-5 (Reasoning model for coding/agents)",
        "gpt-5-mini": "GPT-5 Mini (Fast, cost-efficient)",
        "gpt-5-nano": "GPT-5 Nano (Fastest, lowest cost)",
        "gpt-4.1": "GPT-4.1 (Smartest non-reasoning model)",
        "gpt-4.1-mini": "GPT-4.1 Mini (Fast, cost-effective)",
        "gpt-4.1-nano": "GPT-4.1 Nano (Fastest, lowest cost GPT-4.1)",
        "gpt-4o": "GPT-4o (Multimodal, vision)",
        "gpt-4o-mini": "GPT-4o Mini (Fast multimodal)",
        "o4-mini": "o4-mini (Fast reasoning model)",
        "o3": "o3 (Advanced reasoning)",
    }

    # Available image generation models
    IMAGE_MODELS = {
        "gpt-image-1.5": "GPT Image 1.5 (Latest, best quality)",
        "gpt-image-1": "GPT Image 1 (High quality, editing support)",
        "gpt-image-1-mini": "GPT Image 1 Mini (Cost-efficient)",
        "dall-e-3": "DALL-E 3 (Deprecated)",
    }

    # Default configuration
    DEFAULT_MODEL = "gpt-4o"
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_TEMPERATURE = 0.7
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1.0

    # Models that use max_completion_tokens instead of max_tokens
    NEW_TOKEN_PARAM_MODELS = {"gpt-5.2", "gpt-5.2-pro", "gpt-5.1", "gpt-5", "gpt-5-mini", "gpt-5-nano", "o3", "o4-mini"}

    # Reasoning models that don't support temperature, top_p, or stop
    REASONING_MODELS = {"o3", "o4-mini"}

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        config_path: Optional[str] = None
    ):
        """
        Initialize OpenAI API client.

        Args:
            api_key: OpenAI API key (optional, will check env/config)
            model: OpenAI model to use
            config_path: Path to config.ini file
        """
        self.model_name = model

        # Resolve API key from multiple sources
        self.api_key = self._resolve_api_key(api_key, config_path)

        # Import openai here to avoid import errors if not installed
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package is required. Install with: pip install openai>=1.0.0"
            )

        # Initialize the client
        self.client = OpenAI(api_key=self.api_key)

        # Store configuration for later use
        self.system_instruction = None

    def _resolve_api_key(self, api_key: Optional[str], config_path: Optional[str]) -> str:
        """
        Resolve API key from multiple sources in order of priority:
        1. ComfyUI Settings (comfy.settings.json)
        2. Provided api_key parameter
        3. OPENAI_API_KEY environment variable
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
            settings_key = get_comfy_setting("ERPK.OPENAI_API_KEY")
            if settings_key:
                return settings_key
        except (ImportError, ValueError):
            pass

        # Priority 2: Direct parameter
        if api_key and api_key.strip():
            return api_key.strip()

        # Priority 2: Environment variable
        env_key = os.getenv("OPENAI_API_KEY")
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
            if "openai" in config and "api_key" in config["openai"]:
                return config["openai"]["api_key"]

        raise ValueError(
            "No API key found. Please provide via:\n"
            "1. ComfyUI Settings (Settings > ERPK > API Keys)\n"
            "2. api_key parameter\n"
            "3. OPENAI_API_KEY environment variable\n"
            "4. config.ini file in openai/ directory"
        )

    def update_config(self, system_instruction: Optional[str] = None):
        """
        Update client configuration.

        Args:
            system_instruction: System-level instruction for the model
        """
        if system_instruction:
            self.system_instruction = system_instruction

    def generate_content(
        self,
        prompt: str,
        images: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        top_p: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None,
        response_format: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate content using OpenAI API.

        Args:
            prompt: Text prompt
            images: Optional list of image data dicts for vision tasks
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            model: Optional model override (uses client default if not specified)
            top_p: Nucleus sampling threshold (None to disable)
            stop_sequences: List of sequences where generation stops
            response_format: Output format (e.g., {"type": "json_object"})
            **kwargs: Additional parameters

        Returns:
            Response dict with 'text' and metadata
        """
        from openai import APIError, RateLimitError, APIConnectionError

        max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS
        temperature = temperature if temperature is not None else self.DEFAULT_TEMPERATURE
        model_to_use = model or self.model_name

        # Build messages
        messages = []

        # Add system instruction if set
        if self.system_instruction:
            messages.append({"role": "system", "content": self.system_instruction})

        # Build user message content
        if images:
            # Multimodal message with images
            content = []
            for img_data in images:
                content.append({
                    "type": "image_url",
                    "image_url": img_data
                })
            content.append({"type": "text", "text": prompt})
            messages.append({"role": "user", "content": content})
        else:
            # Text-only message
            messages.append({"role": "user", "content": prompt})

        # Build request parameters
        params = {
            "model": model_to_use,
            "messages": messages,
        }

        # Use correct token parameter based on model
        if model_to_use in self.NEW_TOKEN_PARAM_MODELS:
            params["max_completion_tokens"] = max_tokens
        else:
            params["max_tokens"] = max_tokens

        # Reasoning models don't support temperature, top_p, or stop
        is_reasoning = model_to_use in self.REASONING_MODELS

        if not is_reasoning:
            params["temperature"] = temperature
            if top_p is not None:
                params["top_p"] = top_p
            if stop_sequences:
                params["stop"] = stop_sequences

        if response_format:
            params["response_format"] = response_format

        # Retry logic with exponential backoff
        retry_delay = self.INITIAL_RETRY_DELAY
        last_exception = None

        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(**params)

                # Extract text from response
                text = response.choices[0].message.content or ""
                finish_reason = response.choices[0].finish_reason

                return {
                    "text": text,
                    "blocked": False,
                    "finish_reason": finish_reason,
                    "usage": {
                        "input_tokens": response.usage.prompt_tokens,
                        "output_tokens": response.usage.completion_tokens,
                    }
                }

            except RateLimitError as e:
                last_exception = e
                if attempt < self.MAX_RETRIES - 1:
                    print(f"[OpenAI] Rate limit hit, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2

            except APIConnectionError as e:
                last_exception = e
                if attempt < self.MAX_RETRIES - 1:
                    print(f"[OpenAI] Connection error, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2

            except APIError as e:
                # Check for content policy violation
                if hasattr(e, 'code') and e.code == 'content_policy_violation':
                    return {
                        "text": "",
                        "blocked": True,
                        "finish_reason": "CONTENT_FILTER",
                        "error": str(e)
                    }
                last_exception = e
                if attempt < self.MAX_RETRIES - 1:
                    print(f"[OpenAI] API error, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2

        # All retries exhausted
        raise Exception(f"Request failed after {self.MAX_RETRIES} attempts: {last_exception}")

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        top_p: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None,
        response_format: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a chat completion request with full message history.

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            model: Optional model override
            top_p: Nucleus sampling threshold
            stop_sequences: List of stop sequences
            response_format: Output format specification
            **kwargs: Additional parameters

        Returns:
            Response dict with 'text' and metadata
        """
        from openai import APIError, RateLimitError, APIConnectionError

        max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS
        temperature = temperature if temperature is not None else self.DEFAULT_TEMPERATURE
        model_to_use = model or self.model_name

        # Prepend system instruction if set and not already in messages
        full_messages = list(messages)
        if self.system_instruction:
            if not full_messages or full_messages[0].get("role") != "system":
                full_messages.insert(0, {"role": "system", "content": self.system_instruction})

        # Build request parameters
        params = {
            "model": model_to_use,
            "messages": full_messages,
        }

        # Use correct token parameter based on model
        if model_to_use in self.NEW_TOKEN_PARAM_MODELS:
            params["max_completion_tokens"] = max_tokens
        else:
            params["max_tokens"] = max_tokens

        # Reasoning models don't support temperature, top_p, or stop
        is_reasoning = model_to_use in self.REASONING_MODELS

        if not is_reasoning:
            params["temperature"] = temperature
            if top_p is not None:
                params["top_p"] = top_p
            if stop_sequences:
                params["stop"] = stop_sequences

        if response_format:
            params["response_format"] = response_format

        # Retry logic
        retry_delay = self.INITIAL_RETRY_DELAY
        last_exception = None

        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(**params)

                text = response.choices[0].message.content or ""
                finish_reason = response.choices[0].finish_reason

                return {
                    "text": text,
                    "blocked": False,
                    "finish_reason": finish_reason,
                    "usage": {
                        "input_tokens": response.usage.prompt_tokens,
                        "output_tokens": response.usage.completion_tokens,
                    }
                }

            except RateLimitError as e:
                last_exception = e
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2

            except (APIConnectionError, APIError) as e:
                last_exception = e
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2

        raise Exception(f"Chat request failed after {self.MAX_RETRIES} attempts: {last_exception}")

    def generate_image(
        self,
        prompt: str,
        model: str = "gpt-image-1",
        size: str = "1024x1024",
        quality: str = "auto",
        background: str = "auto",
        n: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate an image using OpenAI's image generation API.

        Args:
            prompt: Text description of image to generate
            model: Image model (gpt-image-1, dall-e-3, dall-e-2)
            size: Image size (1024x1024, 1024x1536, 1536x1024, etc.)
            quality: Image quality (auto, low, medium, high - gpt-image-1 only)
            background: Background type (auto, transparent, opaque - gpt-image-1 only)
            n: Number of images to generate
            **kwargs: Additional parameters

        Returns:
            Dict with 'images' (list of base64 data) and metadata
        """
        from openai import APIError

        params = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "n": n,
        }

        # Model-specific parameters
        if model in ["gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini"]:
            if quality != "auto":
                params["quality"] = quality
            if background != "auto":
                params["background"] = background
            # GPT Image models return base64 by default
            params["response_format"] = "b64_json"
        elif model == "dall-e-3":
            # DALL-E 3 quality options
            if quality in ["hd", "standard"]:
                params["quality"] = quality
            params["response_format"] = "b64_json"
        else:
            params["response_format"] = "b64_json"

        try:
            response = self.client.images.generate(**params)

            images = []
            for img in response.data:
                if hasattr(img, 'b64_json') and img.b64_json:
                    images.append(img.b64_json)

            return {
                "images": images,
                "revised_prompt": response.data[0].revised_prompt if hasattr(response.data[0], 'revised_prompt') else None
            }

        except APIError as e:
            if hasattr(e, 'code') and e.code == 'content_policy_violation':
                return {
                    "images": [],
                    "blocked": True,
                    "error": str(e)
                }
            raise

    def edit_image(
        self,
        image_data: bytes,
        prompt: str,
        mask_data: Optional[bytes] = None,
        model: str = "gpt-image-1",
        size: str = "1024x1024",
        quality: str = "auto",
        n: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Edit an image using OpenAI's image editing API.

        Args:
            image_data: Original image as bytes (PNG format)
            prompt: Text description of desired edits
            mask_data: Optional mask as bytes (PNG with transparency)
            model: Image model (gpt-image-1 recommended)
            size: Output image size
            quality: Image quality (gpt-image-1 only)
            n: Number of images to generate
            **kwargs: Additional parameters

        Returns:
            Dict with 'images' (list of base64 data) and metadata
        """
        from openai import APIError

        # Prepare image file
        image_file = ("image.png", image_data, "image/png")

        params = {
            "model": model,
            "image": image_file,
            "prompt": prompt,
            "size": size,
            "n": n,
            "response_format": "b64_json",
        }

        # Add mask if provided
        if mask_data:
            mask_file = ("mask.png", mask_data, "image/png")
            params["mask"] = mask_file

        # Model-specific parameters
        if model in ["gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini"] and quality != "auto":
            params["quality"] = quality

        try:
            response = self.client.images.edit(**params)

            images = []
            for img in response.data:
                if hasattr(img, 'b64_json') and img.b64_json:
                    images.append(img.b64_json)

            return {"images": images}

        except APIError as e:
            if hasattr(e, 'code') and e.code == 'content_policy_violation':
                return {
                    "images": [],
                    "blocked": True,
                    "error": str(e)
                }
            raise
