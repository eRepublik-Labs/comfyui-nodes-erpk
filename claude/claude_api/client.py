"""
Claude API Client

Provides a client wrapper for interacting with Anthropic's Claude API.
Supports streaming, prompt caching, and error handling with retries.
"""

import os
import time
from typing import Dict, Any, Generator, Optional
from anthropic import Anthropic, AnthropicError, APIError, RateLimitError, APIConnectionError
import configparser


class ClaudeClient:
    """
    Client for interacting with Claude API.

    Features:
    - Multi-source API key management (input → env → config)
    - Streaming support with fallback to synchronous
    - Error handling with exponential backoff
    - Prompt caching configuration
    - Token usage tracking
    """

    # Default configuration
    DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
    DEFAULT_MAX_TOKENS = 1024
    DEFAULT_TEMPERATURE = 0.7
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1.0  # seconds

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        enable_streaming: bool = False,
        enable_caching: bool = True,
        config_path: Optional[str] = None
    ):
        """
        Initialize Claude API client.

        Args:
            api_key: Anthropic API key (optional, will check env/config)
            model: Claude model to use
            enable_streaming: Enable streaming responses
            enable_caching: Enable prompt caching for cost optimization
            config_path: Path to config.ini file
        """
        self.model = model
        self.enable_streaming = enable_streaming
        self.enable_caching = enable_caching

        # Resolve API key from multiple sources
        self.api_key = self._resolve_api_key(api_key, config_path)

        # Initialize Anthropic client with optional beta headers
        client_kwargs = {"api_key": self.api_key}
        if enable_caching:
            try:
                # Try to enable prompt caching beta feature
                client_kwargs["default_headers"] = {
                    "anthropic-beta": "prompt-caching-2024-07-31"
                }
            except Exception as e:
                print(f"[Claude] Warning: Could not enable prompt caching: {e}")

        self.client = Anthropic(**client_kwargs)

        # Track usage statistics
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.cache_read_tokens = 0
        self.cache_creation_tokens = 0

    def _resolve_api_key(self, api_key: Optional[str], config_path: Optional[str]) -> str:
        """
        Resolve API key from multiple sources in order of priority:
        1. Provided api_key parameter
        2. ANTHROPIC_API_KEY environment variable
        3. config.ini file

        Args:
            api_key: API key provided directly
            config_path: Path to config.ini

        Returns:
            Resolved API key

        Raises:
            ValueError: If no API key found
        """
        # Priority 1: Direct parameter
        if api_key and api_key.strip():
            return api_key.strip()

        # Priority 2: Environment variable
        env_key = os.getenv("ANTHROPIC_API_KEY")
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
            if "claude" in config and "api_key" in config["claude"]:
                return config["claude"]["api_key"]

        raise ValueError(
            "No API key found. Please provide via:\n"
            "1. api_key parameter\n"
            "2. ANTHROPIC_API_KEY environment variable\n"
            "3. config.ini file in claude/ directory"
        )

    def send_request(
        self,
        messages: list,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a synchronous request to Claude API with retry logic.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            model: Override default model
            **kwargs: Additional parameters for the API

        Returns:
            API response dict with 'content', 'usage', etc.

        Raises:
            APIError: If request fails after retries
        """
        model = model or self.model
        max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS
        temperature = temperature if temperature is not None else self.DEFAULT_TEMPERATURE

        # Build request parameters
        params = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        if system:
            params["system"] = system

        # Merge additional kwargs
        params.update(kwargs)

        # Note: Prompt caching is enabled via client initialization headers

        # Retry logic with exponential backoff
        retry_delay = self.INITIAL_RETRY_DELAY
        last_exception = None

        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.client.messages.create(**params)

                # Track token usage
                usage = response.usage
                self.total_input_tokens += usage.input_tokens
                self.total_output_tokens += usage.output_tokens
                if hasattr(usage, 'cache_read_input_tokens'):
                    self.cache_read_tokens += usage.cache_read_input_tokens or 0
                if hasattr(usage, 'cache_creation_input_tokens'):
                    self.cache_creation_tokens += usage.cache_creation_input_tokens or 0

                return response

            except RateLimitError as e:
                last_exception = e
                if attempt < self.MAX_RETRIES - 1:
                    print(f"[Claude] Rate limit hit, retrying in {retry_delay}s... (attempt {attempt + 1}/{self.MAX_RETRIES})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff

            except APIConnectionError as e:
                last_exception = e
                if attempt < self.MAX_RETRIES - 1:
                    print(f"[Claude] Connection error, retrying in {retry_delay}s... (attempt {attempt + 1}/{self.MAX_RETRIES})")
                    time.sleep(retry_delay)
                    retry_delay *= 2

            except APIError as e:
                # Don't retry on client errors (4xx except 429)
                if hasattr(e, 'status_code') and 400 <= e.status_code < 500 and e.status_code != 429:
                    raise
                last_exception = e
                if attempt < self.MAX_RETRIES - 1:
                    print(f"[Claude] API error, retrying in {retry_delay}s... (attempt {attempt + 1}/{self.MAX_RETRIES})")
                    time.sleep(retry_delay)
                    retry_delay *= 2

        # All retries exhausted
        raise APIError(f"Request failed after {self.MAX_RETRIES} attempts") from last_exception

    def send_request_streaming(
        self,
        messages: list,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Send a streaming request to Claude API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            model: Override default model
            **kwargs: Additional parameters for the API

        Yields:
            Text chunks as they arrive

        Raises:
            APIError: If streaming fails
        """
        model = model or self.model
        max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS
        temperature = temperature if temperature is not None else self.DEFAULT_TEMPERATURE

        # Build request parameters
        params = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        if system:
            params["system"] = system

        # Merge additional kwargs
        params.update(kwargs)

        # Note: Prompt caching is enabled via client initialization headers

        try:
            with self.client.messages.stream(**params) as stream:
                for text in stream.text_stream:
                    yield text

                # Get final message for usage tracking
                final_message = stream.get_final_message()
                usage = final_message.usage
                self.total_input_tokens += usage.input_tokens
                self.total_output_tokens += usage.output_tokens
                if hasattr(usage, 'cache_read_input_tokens'):
                    self.cache_read_tokens += usage.cache_read_input_tokens or 0
                if hasattr(usage, 'cache_creation_input_tokens'):
                    self.cache_creation_tokens += usage.cache_creation_input_tokens or 0

        except AnthropicError as e:
            raise APIError(f"Streaming request failed: {str(e)}") from e

    def count_tokens(self, messages: list, system: Optional[str] = None) -> int:
        """
        Count tokens in a message list using Anthropic's API.

        Args:
            messages: List of message dicts
            system: Optional system prompt

        Returns:
            Token count
        """
        try:
            # Use Anthropic's beta token counting API
            params = {
                "model": self.model,
                "messages": messages
            }
            if system:
                params["system"] = system

            response = self.client.beta.messages.count_tokens(**params)
            return response.input_tokens

        except Exception as e:
            # Fallback to rough estimation if API fails
            print(f"[Claude] Token counting API failed, using estimation: {e}")
            total_text = ""
            if system:
                total_text += system + " "
            for msg in messages:
                content = msg.get("content", "")
                if isinstance(content, str):
                    total_text += content + " "
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            total_text += item.get("text", "") + " "
            # Rough estimate: ~4 characters per token
            return len(total_text) // 4

    def get_usage_stats(self) -> Dict[str, int]:
        """
        Get cumulative token usage statistics.

        Returns:
            Dict with token usage counts and cost estimates
        """
        # Pricing for Claude Sonnet 4.5 (per million tokens)
        # Updated: October 2025
        # Source: https://www.anthropic.com/pricing
        INPUT_PRICE = 3.0
        OUTPUT_PRICE = 15.0
        CACHE_READ_PRICE = 0.3  # 0.1x of input price

        input_cost = (self.total_input_tokens / 1_000_000) * INPUT_PRICE
        output_cost = (self.total_output_tokens / 1_000_000) * OUTPUT_PRICE
        cache_read_cost = (self.cache_read_tokens / 1_000_000) * CACHE_READ_PRICE
        total_cost = input_cost + output_cost + cache_read_cost

        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_creation_tokens": self.cache_creation_tokens,
            "total_cost_usd": round(total_cost, 4),
            "input_cost_usd": round(input_cost, 4),
            "output_cost_usd": round(output_cost, 4),
            "cache_savings_usd": round((self.cache_read_tokens / 1_000_000) * (INPUT_PRICE - CACHE_READ_PRICE), 4)
        }

    def reset_usage_stats(self):
        """Reset token usage statistics."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.cache_read_tokens = 0
        self.cache_creation_tokens = 0
