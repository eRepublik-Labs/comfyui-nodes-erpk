"""
Claude API Client

Provides a client wrapper for interacting with Anthropic's Claude API.
Supports streaming, prompt caching, and error handling with retries.

Public methods that perform HTTP I/O are async so ComfyUI's executor can
interleave concurrent API nodes. The underlying HTTP work uses the synchronous
Anthropic SDK via asyncio.to_thread, preserving the existing retry machinery
while releasing the event loop during network I/O.
"""

import asyncio
import functools
import json
import os
import threading
import time
from typing import Dict, Any, Generator, Optional
from anthropic import Anthropic, APIError, RateLimitError, APIConnectionError
import configparser

from ..models import DEFAULT_TEXT_MODEL


@functools.lru_cache(maxsize=1)
def model_prices() -> Dict[str, Dict[str, float]]:
    """Per-MTok USD prices from pricing.json, keyed by model ID."""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pricing.json")
    with open(path) as f:
        return json.load(f)["models"]


def response_text(response) -> str:
    """Join the text blocks of a Messages response.

    Thinking-only models return a thinking block ahead of the text, so the
    first block is not necessarily the answer.
    """
    blocks = getattr(response, "content", None) or []
    texts = [block.text for block in blocks if getattr(block, "type", None) == "text"]
    if not texts:
        raise ValueError("Claude returned no text block")
    return "".join(texts)


class ClaudeClient:
    """
    Client for interacting with Claude API.

    Features:
    - API key resolution (ComfyUI Settings → api_key → config.ini)
    - Streaming and non-streaming requests
    - Retry with exponential backoff on 429, connection errors and 5xx
    - Automatic prompt caching (top-level cache_control)
    - Token usage tracking
    """

    # Default configuration
    DEFAULT_MODEL = DEFAULT_TEXT_MODEL
    DEFAULT_MAX_TOKENS = 1024
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1.0  # seconds

    # Every offered model (Claude 5 and later) runs adaptive thinking and returns
    # 400 on a non-default temperature/top_p/top_k, so none are ever sent.
    # "summarized" surfaces the thinking text; the API default is "omitted".
    THINKING = {"type": "adaptive", "display": "summarized"}

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
            api_key: Anthropic API key (optional, will check settings/config)
            model: Claude model to use
            enable_streaming: Enable streaming responses
            enable_caching: Send automatic prompt caching (top-level cache_control)
            config_path: Path to config.ini file
        """
        self.model = model
        self.enable_streaming = enable_streaming
        self.enable_caching = enable_caching

        # Resolve API key from multiple sources
        self.api_key = self._resolve_api_key(api_key, config_path)

        self.client = Anthropic(api_key=self.api_key)

        # Track usage statistics. When one client is shared across concurrent
        # nodes these counters are updated from asyncio.to_thread worker threads,
        # so guard the non-atomic += with a lock to avoid lost increments.
        self._usage_lock = threading.Lock()
        self.reset_usage_stats()

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
            settings_key = get_comfy_setting("ERPK.ANTHROPIC_API_KEY")
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
            if "claude" in config and "api_key" in config["claude"]:
                return config["claude"]["api_key"]

        raise ValueError(
            "No API key found. Please provide via:\n"
            "1. ComfyUI Settings (Settings > ERPK > API Keys)\n"
            "2. api_key parameter\n"
            "3. config.ini file in claude/ directory"
        )

    def _build_params(
        self,
        messages: list,
        system: Optional[str],
        max_tokens: Optional[int],
        model: Optional[str],
        effort: Optional[str],
        kwargs: Dict[str, Any],
    ) -> Dict[str, Any]:
        params = {
            "model": model or self.model,
            "max_tokens": max_tokens or self.DEFAULT_MAX_TOKENS,
            "messages": messages,
            "thinking": self.THINKING,
        }
        if system:
            params["system"] = system
        if self.enable_caching:
            # Automatic caching: the API places the breakpoint on the last
            # cacheable block. Prompts below the model's minimum are not cached.
            params["cache_control"] = {"type": "ephemeral"}
        params.update(kwargs)
        if effort:
            params["output_config"] = {**params.get("output_config", {}), "effort": effort}
        return params

    def _record_usage(self, message) -> None:
        """Add a response's tokens and cost, priced by the model that answered.

        usage.input_tokens excludes cached tokens, which are billed separately:
        cache reads at the hit price, cache creation at the 5-minute write price
        (automatic caching uses the 5-minute TTL).
        """
        usage = message.usage
        tokens = {
            "input": usage.input_tokens,
            "output": usage.output_tokens,
            "cache_read": getattr(usage, "cache_read_input_tokens", None) or 0,
            "cache_write": getattr(usage, "cache_creation_input_tokens", None) or 0,
        }
        prices = model_prices().get(message.model)
        with self._usage_lock:
            self.total_input_tokens += tokens["input"]
            self.total_output_tokens += tokens["output"]
            self.cache_read_tokens += tokens["cache_read"]
            self.cache_creation_tokens += tokens["cache_write"]
            if prices is None:
                print(f"[Claude] Warning: no price for model {message.model!r}; its usage is not costed")
                self.unpriced_models.add(message.model)
                return
            per_mtok = {
                "input": prices["input_price_per_mtok"],
                "output": prices["output_price_per_mtok"],
                "cache_read": prices["cache_read_price_per_mtok"],
                "cache_write": prices["cache_write_5m_price_per_mtok"],
            }
            for kind, count in tokens.items():
                self.costs_usd[kind] += count / 1_000_000 * per_mtok[kind]
            self.cache_savings_usd += tokens["cache_read"] / 1_000_000 * (per_mtok["input"] - per_mtok["cache_read"])

    def _send_request_sync(
        self,
        messages: list,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        effort: Optional[str] = None,
        **kwargs
    ):
        params = self._build_params(messages, system, max_tokens, model, effort, kwargs)

        # Retry logic with exponential backoff
        retry_delay = self.INITIAL_RETRY_DELAY
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.client.messages.create(**params)
                self._record_usage(response)
                return response

            except APIError as e:
                retryable = isinstance(e, (RateLimitError, APIConnectionError)) or not (
                    400 <= getattr(e, "status_code", 500) < 500
                )
                if not retryable or attempt == self.MAX_RETRIES - 1:
                    raise
                print(f"[Claude] {type(e).__name__}, retrying in {retry_delay}s... (attempt {attempt + 1}/{self.MAX_RETRIES})")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff

    async def send_request(
        self,
        messages: list,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        effort: Optional[str] = None,
        **kwargs
    ):
        """
        Send a request to Claude API with retry logic.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system: Optional system prompt
            max_tokens: Maximum tokens to generate (thinking counts toward it)
            model: Override default model
            effort: output_config.effort level; None leaves the model default
            **kwargs: Additional Messages API parameters

        Returns:
            The SDK's Message object

        Raises:
            anthropic.APIError: The SDK's own error, once retries are exhausted
                or immediately for a non-retryable 4xx
        """
        return await asyncio.to_thread(
            self._send_request_sync,
            messages,
            system=system,
            max_tokens=max_tokens,
            model=model,
            effort=effort,
            **kwargs,
        )

    def send_request_streaming(
        self,
        messages: list,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        effort: Optional[str] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Send a streaming request to Claude API.

        Takes the same arguments as send_request.

        Yields:
            Text chunks as they arrive (thinking deltas are not yielded)

        Raises:
            anthropic.APIError: The SDK's own error
        """
        params = self._build_params(messages, system, max_tokens, model, effort, kwargs)
        with self.client.messages.stream(**params) as stream:
            for text in stream.text_stream:
                yield text
            self._record_usage(stream.get_final_message())

    def _count_tokens_sync(self, messages: list, system: Optional[str] = None) -> int:
        try:
            params = {
                "model": self.model,
                "messages": messages
            }
            if system:
                params["system"] = system

            response = self.client.messages.count_tokens(**params)
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

    async def count_tokens(self, messages: list, system: Optional[str] = None) -> int:
        """
        Count tokens in a message list using Anthropic's API.

        Args:
            messages: List of message dicts
            system: Optional system prompt

        Returns:
            Token count
        """
        return await asyncio.to_thread(self._count_tokens_sync, messages, system)

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get cumulative token usage and cost, each response priced by its own model.

        Returns:
            Dict with token counts, USD costs (rounded to 4 places) and any
            models that answered but have no entry in pricing.json
        """
        with self._usage_lock:
            costs = dict(self.costs_usd)
            return {
                "input_tokens": self.total_input_tokens,
                "output_tokens": self.total_output_tokens,
                "cache_read_tokens": self.cache_read_tokens,
                "cache_creation_tokens": self.cache_creation_tokens,
                "input_cost_usd": round(costs["input"], 4),
                "output_cost_usd": round(costs["output"], 4),
                "cache_read_cost_usd": round(costs["cache_read"], 4),
                "cache_write_cost_usd": round(costs["cache_write"], 4),
                "total_cost_usd": round(sum(costs.values()), 4),
                "cache_savings_usd": round(self.cache_savings_usd, 4),
                "unpriced_models": sorted(self.unpriced_models),
            }

    def reset_usage_stats(self):
        """Reset token usage statistics."""
        with self._usage_lock:
            self.total_input_tokens = 0
            self.total_output_tokens = 0
            self.cache_read_tokens = 0
            self.cache_creation_tokens = 0
            self.costs_usd = {"input": 0.0, "output": 0.0, "cache_read": 0.0, "cache_write": 0.0}
            self.cache_savings_usd = 0.0
            self.unpriced_models = set()
