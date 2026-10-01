# ABOUTME: OpenAI API client using the official openai SDK
# ABOUTME: Handles authentication, chat completions, and image generation

import asyncio
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
    - Image generation and editing with GPT Image models
    """

    # Available text/vision models
    MODELS = {
        "gpt-6.1-sol": "GPT-6.1 Sol (Default, 1.05M context, 128K output, $2/$10 per MTok)",
        "gpt-5.6-sol": "GPT-5.6 Sol (Current flagship, highest capability tier)",
        "gpt-5.6-terra": "GPT-5.6 Terra (Balanced GPT-5.6 tier)",
        "gpt-5.6-luna": "GPT-5.6 Luna (Fast, cost-efficient GPT-5.6 tier)",
        "gpt-6-astra": "GPT-6 Astra (Top tier above Sol, 1.05M context, $10/$50 per MTok)",
        "gpt-6-sol": "GPT-6 Sol (1.05M context, $2/$10 per MTok)",
        "gpt-6-luna": "GPT-6 Luna (Most efficient GPT-6 tier, 1.05M context, $0.10/$0.50 per MTok)",
        "chat-latest": "ChatGPT Instant (Non-reasoning, 400K context, $5/$30 per MTok)",
    }

    # Available image generation models
    IMAGE_MODELS = {
        "gpt-image-2.5-sunburst": "GPT Image 2.5 Sunburst (Highest quality, xhigh/max quality tiers)",
        "gpt-image-2.5-flare": "GPT Image 2.5 Flare (Fastest 2.5 tier, xhigh/max quality tiers)",
        "gpt-image-2": "GPT Image 2 (Latest flagship, 4K, multilingual text)",
    }

    # Image models on the GPT Image family — share parameter conventions
    # (quality + background). Any other model ID takes the legacy
    # response_format path.
    GPT_IMAGE_MODELS = {
        "gpt-image-2.5-sunburst", "gpt-image-2.5-flare",
        "gpt-image-2",
    }

    # Models that accept background="transparent". gpt-image-2 returns 400
    # "Transparent background is not supported for this model." (measured
    # 2026-10-01); both 2.5 models returned RGBA PNGs with real alpha.
    TRANSPARENT_BACKGROUND_MODELS = {"gpt-image-2.5-sunburst", "gpt-image-2.5-flare"}

    # gpt-image-2 and the 2.5 models always process at high fidelity, reject
    # the input_fidelity param (400 invalid_input_fidelity_model, measured
    # 2026-09-21 despite the reference naming only gpt-image-2), and share
    # the same size envelope.
    GPT_IMAGE_2_MODELS = {"gpt-image-2.5-sunburst", "gpt-image-2.5-flare", "gpt-image-2"}

    # Only GPT Image 2.5 accepts the xhigh and max quality tiers; earlier GPT
    # Image models stop at high.
    EXTENDED_QUALITY_MODELS = {"gpt-image-2.5-sunburst", "gpt-image-2.5-flare"}

    # gpt-image-2 size constraints (from OpenAI docs):
    # - max edge <= 3840px, both edges multiples of 16
    # - aspect ratio (long:short) <= 3:1
    # - total pixels between 655,360 and 8,294,400
    GPT_IMAGE_2_MIN_PIXELS = 655_360
    GPT_IMAGE_2_MAX_PIXELS = 8_294_400
    GPT_IMAGE_2_MAX_EDGE = 3840

    # Default configuration
    DEFAULT_MODEL = "gpt-6.1-sol"
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_TEMPERATURE = 0.7
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1.0

    # reasoning_effort values the API rejects for a model. gpt-5.6 Sol/Terra/
    # Luna and gpt-6 Sol/Luna accept none/low/medium/high/xhigh; gpt-6-astra
    # accepts low/medium/high/xhigh (measured 2026-09-23), as does gpt-6.1-sol
    # (measured 2026-10-01). Rejected values clamp to low.
    UNSUPPORTED_EFFORT = {
        "gpt-6.1-sol": {"minimal", "none"},
        "gpt-5.6-sol": {"minimal"},
        "gpt-5.6-terra": {"minimal"},
        "gpt-5.6-luna": {"minimal"},
        "gpt-6-astra": {"minimal", "none"},
        "gpt-6-sol": {"minimal"},
        "gpt-6-luna": {"minimal"},
    }

    # Codes the API uses to refuse on safety grounds. The images endpoints
    # return moderation_blocked; the chat path has long reported
    # content_policy_violation.
    MODERATION_CODES = ("moderation_blocked", "content_policy_violation")

    @classmethod
    def _moderation_block(cls, error):
        """Return the refusal's detail, or None when the error is something else.

        Detail carries `stage` ("input" when the prompt was refused, "output"
        when the finished image was) and coarse `categories`. Both are
        optional in the response, so both may be absent.
        """
        if getattr(error, "code", None) not in cls.MODERATION_CODES:
            return None

        details = {}
        body = getattr(error, "body", None)
        if isinstance(body, dict):
            inner = body.get("error")
            if isinstance(inner, dict) and isinstance(inner.get("moderation_details"), dict):
                details = inner["moderation_details"]

        return {
            "code": getattr(error, "code", None),
            "stage": details.get("moderation_stage"),
            "categories": list(details.get("categories") or []),
            "message": str(error),
        }

    @staticmethod
    def _moderation_message(block) -> str:
        """Compose the sentence a node shows when a request is refused."""
        stage = block.get("stage")
        where = {
            "input": "The prompt was refused",
            "output": "The prompt passed but the generated image was refused",
        }.get(stage, "The request was refused")

        parts = [f"{where} by OpenAI's safety system."]
        if block.get("categories"):
            parts.append(f"Categories: {', '.join(block['categories'])}.")
        if stage == "output":
            parts.append("Rewording may not help; try a different subject.")
        elif stage == "input":
            parts.append("Try rewording the prompt.")
        parts.append(block.get("message", ""))
        return " ".join(p for p in parts if p)

    @classmethod
    def _effort_for(cls, model: str, effort: str) -> str:
        """Clamp a reasoning_effort the model does not document down to low."""
        if effort in cls.UNSUPPORTED_EFFORT.get(model, ()):
            print(f"[OpenAI] {model} does not support reasoning_effort '{effort}'; using 'low'")
            return "low"
        return effort

    @classmethod
    def _quality_for(cls, model: str, quality: str) -> str:
        """Clamp xhigh/max down to high on models that stop at high."""
        if quality in ("xhigh", "max") and model not in cls.EXTENDED_QUALITY_MODELS:
            print(f"[OpenAI] {model} supports quality up to 'high'; using 'high' instead of '{quality}'")
            return "high"
        return quality

    @staticmethod
    def _output_format_params(output_format: str, output_compression: int) -> Dict[str, Any]:
        """images.generate / images.edit params for the output file format.

        png is the API default and takes no compression, so it sends nothing;
        output_compression applies only to jpeg and webp.
        """
        if output_format in ("jpeg", "webp"):
            return {"output_format": output_format, "output_compression": output_compression}
        return {}

    # Models that use max_completion_tokens instead of max_tokens
    NEW_TOKEN_PARAM_MODELS = {
        "gpt-6.1-sol",
        "gpt-6-astra", "gpt-6-sol", "gpt-6-luna",
        "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna",
        "chat-latest",
    }

    # Reasoning models that support reasoning_effort parameter
    REASONING_MODELS = {
        "gpt-6.1-sol",
        "gpt-6-astra", "gpt-6-sol", "gpt-6-luna",
        "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna",
    }

    # Models that reject temperature, top_p and stop on chat.completions.
    # temperature other than 1 400s ("Only the default (1) value is
    # supported") and top_p/stop 400 as unsupported_parameter (measured on
    # gpt-6.1-sol and chat-latest 2026-10-01, gpt-6 tiers 2026-09-23; the
    # gpt-5.6 tiers have never been sent them).
    # chat-latest is here but not in REASONING_MODELS: it rejects sampling
    # params yet takes no reasoning_effort either.
    NO_SAMPLING_MODELS = {
        "gpt-6.1-sol",
        "gpt-6-astra", "gpt-6-sol", "gpt-6-luna",
        "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna",
        "chat-latest",
    }

    # Models that accept the `verbosity` parameter (gpt-5.x and gpt-6 families).
    # When the user selects "default", we omit the param so the model picks its
    # own default. Sending verbosity to a model that doesn't support it returns
    # 400, so we silently drop it for older families.
    VERBOSITY_MODELS = {
        "gpt-6.1-sol",
        "gpt-6-astra", "gpt-6-sol", "gpt-6-luna",
        "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna",
    }

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
            settings_key = get_comfy_setting("ERPK.OPENAI_API_KEY")
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
            if "openai" in config and "api_key" in config["openai"]:
                return config["openai"]["api_key"]

        raise ValueError(
            "No API key found. Please provide via:\n"
            "1. ComfyUI Settings (Settings > ERPK > API Keys)\n"
            "2. api_key parameter\n"
            "3. config.ini file in openai/ directory"
        )

    def update_config(self, system_instruction: Optional[str] = None):
        """
        Update client configuration.

        Args:
            system_instruction: System-level instruction for the model
        """
        if system_instruction:
            self.system_instruction = system_instruction

    def _generate_content_sync(
        self,
        prompt: str,
        images: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        top_p: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None,
        response_format: Optional[Dict] = None,
        seed: Optional[int] = None,
        reasoning_effort: Optional[str] = None,
        verbosity: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
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

        is_reasoning = model_to_use in self.REASONING_MODELS

        if model_to_use not in self.NO_SAMPLING_MODELS:
            params["temperature"] = temperature
            if top_p is not None:
                params["top_p"] = top_p
            if stop_sequences:
                params["stop"] = stop_sequences

        if reasoning_effort and is_reasoning:
            params["reasoning_effort"] = self._effort_for(model_to_use, reasoning_effort)

        if verbosity and verbosity != "default" and model_to_use in self.VERBOSITY_MODELS:
            params["verbosity"] = verbosity

        if response_format:
            params["response_format"] = response_format

        if seed is not None:
            params["seed"] = seed

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
                block = self._moderation_block(e)
                if block:
                    return {
                        "text": "",
                        "blocked": True,
                        "finish_reason": "CONTENT_FILTER",
                        "error": self._moderation_message(block),
                        "moderation_stage": block["stage"],
                        "moderation_categories": block["categories"],
                    }
                last_exception = e
                if attempt < self.MAX_RETRIES - 1:
                    print(f"[OpenAI] API error, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2

        # All retries exhausted
        raise Exception(f"Request failed after {self.MAX_RETRIES} attempts: {last_exception}")

    async def generate_content(
        self,
        prompt: str,
        images: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        top_p: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None,
        response_format: Optional[Dict] = None,
        seed: Optional[int] = None,
        reasoning_effort: Optional[str] = None,
        verbosity: Optional[str] = None,
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
            reasoning_effort: Reasoning depth for reasoning models
                (minimal/low/medium/high/xhigh). Silently dropped for non-reasoning models.
            **kwargs: Additional parameters

        Returns:
            Response dict with 'text' and metadata
        """
        return await asyncio.to_thread(
            self._generate_content_sync, prompt,
            images=images, max_tokens=max_tokens, temperature=temperature,
            model=model, top_p=top_p, stop_sequences=stop_sequences,
            response_format=response_format, seed=seed,
            reasoning_effort=reasoning_effort, verbosity=verbosity, **kwargs
        )

    def _chat_sync(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        top_p: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None,
        response_format: Optional[Dict] = None,
        seed: Optional[int] = None,
        reasoning_effort: Optional[str] = None,
        verbosity: Optional[str] = None,
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
            reasoning_effort: Reasoning depth for reasoning models
                (minimal/low/medium/high/xhigh). Silently dropped for non-reasoning models.
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

        is_reasoning = model_to_use in self.REASONING_MODELS

        if model_to_use not in self.NO_SAMPLING_MODELS:
            params["temperature"] = temperature
            if top_p is not None:
                params["top_p"] = top_p
            if stop_sequences:
                params["stop"] = stop_sequences

        if reasoning_effort and is_reasoning:
            params["reasoning_effort"] = self._effort_for(model_to_use, reasoning_effort)

        if verbosity and verbosity != "default" and model_to_use in self.VERBOSITY_MODELS:
            params["verbosity"] = verbosity

        if response_format:
            params["response_format"] = response_format

        if seed is not None:
            params["seed"] = seed

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

    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        top_p: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None,
        response_format: Optional[Dict] = None,
        seed: Optional[int] = None,
        reasoning_effort: Optional[str] = None,
        verbosity: Optional[str] = None,
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
            reasoning_effort: Reasoning depth for reasoning models
                (minimal/low/medium/high/xhigh). Silently dropped for non-reasoning models.
            **kwargs: Additional parameters

        Returns:
            Response dict with 'text' and metadata
        """
        return await asyncio.to_thread(
            self._chat_sync, messages,
            max_tokens=max_tokens, temperature=temperature, model=model,
            top_p=top_p, stop_sequences=stop_sequences, response_format=response_format,
            seed=seed, reasoning_effort=reasoning_effort, verbosity=verbosity, **kwargs
        )

    @classmethod
    def _check_background(cls, model: str, background: str) -> None:
        """Raise before the call when a model would reject the background (400)."""
        if background == "transparent" and model not in cls.TRANSPARENT_BACKGROUND_MODELS:
            supported = ", ".join(sorted(cls.TRANSPARENT_BACKGROUND_MODELS))
            raise ValueError(
                f"{model} does not support background='transparent'. "
                f"Use {supported}, or set background to auto or opaque."
            )

    def _generate_image_sync(
        self,
        prompt: str,
        model: str = "gpt-image-2",
        size: str = "1024x1024",
        quality: str = "auto",
        background: str = "auto",
        moderation: str = "auto",
        n: int = 1,
        output_format: str = "png",
        output_compression: int = 100,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate an image using OpenAI's image generation API.

        Args:
            prompt: Text description of image to generate
            model: Image model (gpt-image-2.5-sunburst, gpt-image-2.5-flare, gpt-image-2)
            size: Image size (1024x1024, 1024x1536, 1536x1024, etc.)
            quality: Image quality (auto, low, medium, high; xhigh/max on GPT Image 2.5)
            background: Background type (auto, transparent, opaque - GPT Image models only)
            n: Number of images to generate
            **kwargs: Additional parameters

        Returns:
            Dict with 'images' (list of base64 data) and metadata
        """
        from openai import APIError

        # Preflight size validation for gpt-image-2 (stricter than other models)
        if model in self.GPT_IMAGE_2_MODELS:
            self._validate_size_for_gpt_image_2(size, model)

        params = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "n": n,
        }

        # Model-specific parameters
        if model in self.GPT_IMAGE_MODELS:
            if quality != "auto":
                params["quality"] = self._quality_for(model, quality)
            if background != "auto":
                self._check_background(model, background)
                params["background"] = background
            if moderation != "auto":
                params["moderation"] = moderation
            params.update(self._output_format_params(output_format, output_compression))
            # GPT Image models always return base64, do not accept response_format
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
            block = self._moderation_block(e)
            if block:
                return {
                    "images": [],
                    "blocked": True,
                    "error": self._moderation_message(block),
                    "moderation_stage": block["stage"],
                    "moderation_categories": block["categories"],
                }
            raise

    async def generate_image(
        self,
        prompt: str,
        model: str = "gpt-image-2",
        size: str = "1024x1024",
        quality: str = "auto",
        background: str = "auto",
        moderation: str = "auto",
        n: int = 1,
        output_format: str = "png",
        output_compression: int = 100,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate an image using OpenAI's image generation API.

        Args:
            prompt: Text description of image to generate
            model: Image model (gpt-image-2.5-sunburst, gpt-image-2.5-flare, gpt-image-2)
            size: Image size (1024x1024, 1024x1536, 1536x1024, etc.)
            quality: Image quality (auto, low, medium, high; xhigh/max on GPT Image 2.5)
            background: Background type (auto, transparent, opaque - GPT Image models only)
            n: Number of images to generate
            **kwargs: Additional parameters

        Returns:
            Dict with 'images' (list of base64 data) and metadata
        """
        return await asyncio.to_thread(
            self._generate_image_sync, prompt,
            model=model, size=size, quality=quality,
            background=background, moderation=moderation, n=n,
            output_format=output_format, output_compression=output_compression, **kwargs
        )

    def _validate_size_for_gpt_image_2(self, size: str, model: str = "gpt-image-2"):
        """Raise ValueError with a clear, actionable message if `size` doesn't
        meet gpt-image-2's constraints. Called before the API call so users
        get a friendly preflight error instead of a raw 400.
        """
        if size in (None, "", "auto"):
            return  # auto means "let the model choose"; nothing to validate

        try:
            parts = size.lower().split("x")
            width = int(parts[0])
            height = int(parts[1])
        except (ValueError, IndexError):
            return  # malformed size — let the API surface its own error

        if max(width, height) > self.GPT_IMAGE_2_MAX_EDGE:
            raise ValueError(
                f"{model} requires max edge <= {self.GPT_IMAGE_2_MAX_EDGE}px. "
                f"You requested {size} (max edge = {max(width, height)}px)."
            )
        if width % 16 != 0 or height % 16 != 0:
            raise ValueError(
                f"{model} requires both edges to be multiples of 16. "
                f"You requested {size}. Try rounding to nearest 16 "
                f"(e.g., 1024x1024, 1536x1024)."
            )
        long_edge = max(width, height)
        short_edge = min(width, height)
        if short_edge == 0 or (long_edge / short_edge) > 3:
            raise ValueError(
                f"{model} requires aspect ratio (long:short) <= 3:1. "
                f"You requested {size} ({long_edge}:{short_edge})."
            )
        pixels = width * height
        if pixels < self.GPT_IMAGE_2_MIN_PIXELS:
            raise ValueError(
                f"{model} requires at least {self.GPT_IMAGE_2_MIN_PIXELS:,} "
                f"total pixels. You requested {size} = {pixels:,} pixels. "
                f"Pick a larger size (e.g., 1024x1024 = 1,048,576 pixels); "
                f"no GPT Image model returns below 1024x1024."
            )
        if pixels > self.GPT_IMAGE_2_MAX_PIXELS:
            raise ValueError(
                f"{model} max is {self.GPT_IMAGE_2_MAX_PIXELS:,} total pixels. "
                f"You requested {size} = {pixels:,} pixels."
            )

    def _generate_image_via_responses_sync(
        self,
        prompt: str,
        mainline_model: str = DEFAULT_MODEL,
        image_model: str = "gpt-image-2",
        reasoning_effort: str = "none",
        size: str = "auto",
        quality: str = "auto",
        background: str = "auto",
        output_format: str = "png",
        moderation: str = "auto",
        enable_web_search: bool = False,
        action: str = "auto",
        verbosity: str = "default",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate an image via the Responses API with the image_generation tool.

        Adds reasoning effort and optional web search on top of the standard
        image params. The mainline (text/reasoning) model revises the prompt
        before the image model renders. Returns dict with 'images' (list of
        base64 strings), 'revised_prompt', and 'reasoning_summary'.

        Source: https://developers.openai.com/api/docs/guides/responses
        """
        from openai import APIError

        # Preflight: gpt-image-2 size constraints apply regardless of endpoint
        if image_model in self.GPT_IMAGE_2_MODELS:
            self._validate_size_for_gpt_image_2(size)

        # Build the image_generation tool config
        image_tool = {
            "type": "image_generation",
            "model": image_model,
            "action": action,
        }
        if size and size != "auto":
            image_tool["size"] = size
        if quality != "auto":
            image_tool["quality"] = self._quality_for(image_model, quality)
        if output_format and output_format != "png":
            image_tool["output_format"] = output_format
        if moderation != "auto":
            image_tool["moderation"] = moderation
        if background != "auto":
            self._check_background(image_model, background)
            image_tool["background"] = background

        tools = [image_tool]
        if enable_web_search:
            tools.append({"type": "web_search"})

        request_params = {
            "model": mainline_model,
            "input": prompt,
            "tools": tools,
        }

        # The Responses API takes an `instructions` parameter and honours it,
        # so a client configured by the System Instruction node steers the
        # mainline model here. The images endpoints have no equivalent field.
        if self.system_instruction and self.system_instruction.strip():
            request_params["instructions"] = self.system_instruction

        if reasoning_effort and reasoning_effort != "none" and mainline_model in self.REASONING_MODELS:
            request_params["reasoning"] = {
                "effort": self._effort_for(mainline_model, reasoning_effort),
                "summary": "auto",
            }

        if verbosity and verbosity != "default" and mainline_model in self.VERBOSITY_MODELS:
            request_params["verbosity"] = verbosity

        try:
            response = self.client.responses.create(**request_params)

            images = []
            revised_prompts = []
            reasoning_summaries = []
            outputs = getattr(response, "output", None) or []
            for output in outputs:
                out_type = getattr(output, "type", None)
                if out_type == "image_generation_call":
                    result = getattr(output, "result", None)
                    if result:
                        images.append(result)
                    revised = getattr(output, "revised_prompt", None)
                    if revised:
                        revised_prompts.append(revised)
                elif out_type == "reasoning":
                    for part in getattr(output, "summary", []) or []:
                        text = getattr(part, "text", None)
                        if text is None and isinstance(part, dict):
                            text = part.get("text")
                        if text:
                            reasoning_summaries.append(text)

            return {
                "images": images,
                "revised_prompt": "\n\n".join(revised_prompts),
                "reasoning_summary": "\n\n".join(reasoning_summaries),
            }

        except APIError as e:
            block = self._moderation_block(e)
            if block:
                return {
                    "images": [],
                    "blocked": True,
                    "error": self._moderation_message(block),
                    "moderation_stage": block["stage"],
                    "moderation_categories": block["categories"],
                    "revised_prompt": "",
                    "reasoning_summary": "",
                }
            raise

    async def generate_image_via_responses(
        self,
        prompt: str,
        mainline_model: str = DEFAULT_MODEL,
        image_model: str = "gpt-image-2",
        reasoning_effort: str = "none",
        size: str = "auto",
        quality: str = "auto",
        background: str = "auto",
        output_format: str = "png",
        moderation: str = "auto",
        enable_web_search: bool = False,
        action: str = "auto",
        verbosity: str = "default",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate an image via the Responses API with the image_generation tool.

        Adds reasoning effort and optional web search on top of the standard
        image params. The mainline (text/reasoning) model revises the prompt
        before the image model renders. Returns dict with 'images' (list of
        base64 strings), 'revised_prompt', and 'reasoning_summary'.

        Source: https://developers.openai.com/api/docs/guides/responses
        """
        return await asyncio.to_thread(
            self._generate_image_via_responses_sync, prompt,
            mainline_model=mainline_model, image_model=image_model,
            reasoning_effort=reasoning_effort, size=size, quality=quality,
            background=background, output_format=output_format,
            moderation=moderation, enable_web_search=enable_web_search,
            action=action, verbosity=verbosity, **kwargs
        )

    def _edit_image_sync(
        self,
        image_data,
        prompt: str,
        mask_data: Optional[bytes] = None,
        model: str = "gpt-image-2",
        size: str = "1024x1024",
        quality: str = "auto",
        moderation: str = "auto",
        n: int = 1,
        background: str = "auto",
        input_fidelity: str = "auto",
        output_format: str = "png",
        output_compression: int = 100,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Edit an image using OpenAI's image editing API.

        Args:
            image_data: Original image(s) as PNG bytes. Accepts either a single
                `bytes` value OR a list of `bytes` for multi-image editing
                (gpt-image-2 supports up to 16 reference images for character
                and scene continuity).
            prompt: Text description of desired edits
            mask_data: Optional mask as bytes (PNG with transparency). When
                multiple images are provided, mask applies to the first image.
            model: Image model (gpt-image-2 recommended)
            size: Output image size
            quality: Image quality (GPT Image models only)
            n: Number of images to generate
            **kwargs: Additional parameters

        Returns:
            Dict with 'images' (list of base64 data) and metadata
        """
        from openai import APIError

        # Normalize to list for uniform handling
        if isinstance(image_data, (bytes, bytearray)):
            image_list = [bytes(image_data)]
        else:
            image_list = [bytes(b) for b in image_data]

        if not image_list:
            raise ValueError("edit_image requires at least one image")

        # images.edit shares the generation size envelope on these models
        # (measured 2026-09-21: 512x512 and 256x256 400 as "below the current
        # minimum pixel budget", 1536x864 is accepted).
        if model in self.GPT_IMAGE_2_MODELS:
            self._validate_size_for_gpt_image_2(size, model)

        # Single image uses singular multipart field; multi-image uses array.
        # The OpenAI SDK accepts either shape on the `image` parameter.
        if len(image_list) == 1:
            image_param = ("image.png", image_list[0], "image/png")
        else:
            image_param = [
                (f"image_{i}.png", data, "image/png")
                for i, data in enumerate(image_list)
            ]

        params = {
            "model": model,
            "image": image_param,
            "prompt": prompt,
            "size": size,
            "n": n,
        }

        # Add mask if provided (applied to first image for multi-image edits)
        if mask_data:
            mask_file = ("mask.png", mask_data, "image/png")
            params["mask"] = mask_file

        # Model-specific parameters
        if model in self.GPT_IMAGE_MODELS:
            # GPT Image models always return base64, do not accept response_format
            if quality != "auto":
                params["quality"] = self._quality_for(model, quality)
            if moderation != "auto":
                params["moderation"] = moderation
            if background and background != "auto":
                self._check_background(model, background)
                params["background"] = background
            # gpt-image-2 always processes at high fidelity and rejects input_fidelity.
            if input_fidelity and input_fidelity != "auto" and model not in self.GPT_IMAGE_2_MODELS:
                params["input_fidelity"] = input_fidelity
            params.update(self._output_format_params(output_format, output_compression))
        else:
            params["response_format"] = "b64_json"

        try:
            response = self.client.images.edit(**params)

            images = []
            for img in response.data:
                if hasattr(img, 'b64_json') and img.b64_json:
                    images.append(img.b64_json)

            return {"images": images}

        except APIError as e:
            block = self._moderation_block(e)
            if block:
                return {
                    "images": [],
                    "blocked": True,
                    "error": self._moderation_message(block),
                    "moderation_stage": block["stage"],
                    "moderation_categories": block["categories"],
                }
            raise

    async def edit_image(
        self,
        image_data,
        prompt: str,
        mask_data: Optional[bytes] = None,
        model: str = "gpt-image-2",
        size: str = "1024x1024",
        quality: str = "auto",
        moderation: str = "auto",
        n: int = 1,
        background: str = "auto",
        input_fidelity: str = "auto",
        output_format: str = "png",
        output_compression: int = 100,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Edit an image using OpenAI's image editing API.

        Args:
            image_data: Original image(s) as PNG bytes. Accepts either a single
                `bytes` value OR a list of `bytes` for multi-image editing
                (gpt-image-2 supports up to 16 reference images for character
                and scene continuity).
            prompt: Text description of desired edits
            mask_data: Optional mask as bytes (PNG with transparency). When
                multiple images are provided, mask applies to the first image.
            model: Image model (gpt-image-2 recommended)
            size: Output image size
            quality: Image quality (GPT Image models only)
            n: Number of images to generate
            **kwargs: Additional parameters

        Returns:
            Dict with 'images' (list of base64 data) and metadata
        """
        return await asyncio.to_thread(
            self._edit_image_sync, image_data, prompt,
            mask_data=mask_data, model=model, size=size, quality=quality,
            moderation=moderation, n=n, background=background,
            input_fidelity=input_fidelity, output_format=output_format,
            output_compression=output_compression, **kwargs
        )
