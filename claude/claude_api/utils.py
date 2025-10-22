"""
Utilities for Claude API Integration

Provides base request classes, token management, image conversion,
and other utility functions for Claude API interactions.
"""

import base64
import io
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import numpy as np


class BaseRequest(ABC):
    """
    Abstract base class for Claude API requests.

    All request models should inherit from this class and implement
    the required abstract methods.
    """

    @abstractmethod
    def build_payload(self) -> Dict[str, Any]:
        """
        Build the API request payload.

        Returns:
            Dict containing the complete request payload
        """
        pass

    @abstractmethod
    def get_api_path(self) -> str:
        """
        Get the API endpoint path.

        Returns:
            API endpoint path (e.g., "/v1/messages")
        """
        pass

    @abstractmethod
    def field_required(self) -> List[str]:
        """
        Get list of required field names.

        Returns:
            List of required field names
        """
        pass

    def field_order(self) -> List[str]:
        """
        Get the order of fields for serialization.

        Returns:
            List of field names in order
        """
        return []

    def _remove_empty_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove None and empty values from dictionary.

        Args:
            data: Dictionary to clean

        Returns:
            Cleaned dictionary
        """
        return {k: v for k, v in data.items() if v is not None and v != "" and v != []}


class TokenManager:
    """
    Manages token counting and context window handling for Claude models.

    Features:
    - Token counting for messages
    - Context window trimming
    - Reserve tokens for responses
    """

    # Context window sizes for different Claude models
    CONTEXT_WINDOWS = {
        "claude-sonnet-4-5-20250929": 200_000,
        "claude-opus-4": 200_000,
        "claude-haiku-4-5": 200_000,
        "claude-sonnet-3-5": 200_000,
    }

    # Default reserve tokens for response generation
    DEFAULT_RESERVE_TOKENS = 20_000

    def __init__(self, model: str = "claude-sonnet-4-5-20250929"):
        """
        Initialize token manager.

        Args:
            model: Claude model name
        """
        self.model = model
        self.context_window = self.CONTEXT_WINDOWS.get(model, 200_000)

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Uses rough estimation of ~4 characters per token.
        For accurate counting, use ClaudeClient.count_tokens().

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count
        """
        return len(text) // 4

    def estimate_message_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """
        Estimate token count for message list.

        Args:
            messages: List of message dicts with 'content'

        Returns:
            Estimated token count
        """
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total += self.estimate_tokens(content)
            elif isinstance(content, list):
                # Multimodal content (text + images)
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        total += self.estimate_tokens(item.get("text", ""))
                    elif isinstance(item, dict) and item.get("type") == "image":
                        # Images cost ~1600 tokens on average
                        total += 1600
        return total

    def trim_messages_to_fit(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        reserve_tokens: int = DEFAULT_RESERVE_TOKENS,
        keep_recent: int = 4
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Trim message history to fit context window.

        Strategy:
        1. Always keep system message
        2. Always keep last N messages (keep_recent)
        3. Remove oldest messages until we fit

        Args:
            messages: List of message dicts
            system: Optional system prompt
            reserve_tokens: Tokens to reserve for response
            keep_recent: Minimum number of recent messages to keep

        Returns:
            Tuple of (trimmed_messages, removed_count)
        """
        max_tokens = self.context_window - reserve_tokens

        # Estimate current token count
        system_tokens = self.estimate_tokens(system) if system else 0
        message_tokens = self.estimate_message_tokens(messages)
        total_tokens = system_tokens + message_tokens

        if total_tokens <= max_tokens:
            return messages, 0

        # Keep at least the most recent messages
        if len(messages) <= keep_recent:
            print(f"[Claude] Warning: Message history exceeds context window ({total_tokens} tokens) but keeping all {len(messages)} messages")
            return messages, 0

        # Remove oldest messages until we fit
        removed_count = 0
        trimmed = messages[:]

        while total_tokens > max_tokens and len(trimmed) > keep_recent:
            # Remove from the beginning
            removed_msg = trimmed.pop(0)
            removed_count += 1
            removed_tokens = self.estimate_message_tokens([removed_msg])
            total_tokens -= removed_tokens

        if total_tokens > max_tokens:
            print(f"[Claude] Warning: After trimming to {len(trimmed)} messages, still exceeding context window ({total_tokens} tokens)")

        return trimmed, removed_count

    def validate_message_roles(self, messages: List[Dict[str, Any]]) -> bool:
        """
        Validate message role alternation (user/assistant pattern).

        Claude requires messages to alternate between user and assistant,
        starting with user.

        Args:
            messages: List of message dicts with 'role'

        Returns:
            True if valid, False otherwise
        """
        if not messages:
            return False

        # Must start with user
        if messages[0].get("role") != "user":
            return False

        # Must alternate (or have consecutive user messages consolidated)
        expected_role = "user"
        for msg in messages:
            role = msg.get("role")
            if role not in ["user", "assistant"]:
                return False
            # Allow user messages to follow each other (will be consolidated)
            if role == "assistant" and expected_role == "assistant":
                return False
            if role == "assistant":
                expected_role = "user"
            elif role == "user":
                expected_role = "assistant"

        return True

    def consolidate_consecutive_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Consolidate consecutive messages from the same role.

        Args:
            messages: List of message dicts

        Returns:
            Consolidated message list
        """
        if not messages:
            return messages

        consolidated = []
        current_role = None
        current_content = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")

            if role == current_role:
                # Same role, append content
                if isinstance(content, str):
                    current_content.append(content)
                elif isinstance(content, list):
                    current_content.extend(content)
            else:
                # Different role, save previous and start new
                if current_role is not None:
                    if isinstance(current_content[0], str):
                        consolidated_content = "\n\n".join(current_content)
                    else:
                        consolidated_content = current_content
                    consolidated.append({"role": current_role, "content": consolidated_content})

                current_role = role
                current_content = [content]

        # Add the last message
        if current_role is not None:
            if isinstance(current_content[0], str):
                consolidated_content = "\n\n".join(current_content)
            else:
                consolidated_content = current_content
            consolidated.append({"role": current_role, "content": consolidated_content})

        return consolidated


class ImageConverter:
    """
    Handles image conversion between ComfyUI tensors, PIL Images, and base64.

    ComfyUI images are torch.Tensor in format [B, H, W, C] with values in [0, 1].
    """

    @staticmethod
    def tensor_to_pil(tensor) -> Image.Image:
        """
        Convert ComfyUI tensor to PIL Image.

        Args:
            tensor: ComfyUI image tensor [B, H, W, C] or [H, W, C]

        Returns:
            PIL Image
        """
        try:
            import torch
        except ImportError:
            raise ImportError("torch is required for tensor conversion")

        # Handle batch dimension
        if len(tensor.shape) == 4:
            tensor = tensor[0]  # Take first image in batch

        # Convert to numpy and scale to [0, 255]
        array = np.clip(255.0 * tensor.cpu().numpy(), 0, 255).astype(np.uint8)

        # Convert to PIL
        return Image.fromarray(array)

    @staticmethod
    def pil_to_tensor(pil_image: Image.Image):
        """
        Convert PIL Image to ComfyUI tensor.

        Args:
            pil_image: PIL Image

        Returns:
            ComfyUI tensor [1, H, W, C]
        """
        try:
            import torch
        except ImportError:
            raise ImportError("torch is required for tensor conversion")

        # Convert to numpy array and normalize to [0, 1]
        array = np.array(pil_image).astype(np.float32) / 255.0

        # Handle grayscale
        if len(array.shape) == 2:
            array = np.expand_dims(array, axis=-1)

        # Convert to tensor and add batch dimension
        tensor = torch.from_numpy(array).unsqueeze(0)

        return tensor

    @staticmethod
    def pil_to_base64(pil_image: Image.Image, format: str = "PNG") -> str:
        """
        Convert PIL Image to base64 string.

        Args:
            pil_image: PIL Image
            format: Image format (PNG, JPEG, etc.)

        Returns:
            Base64 encoded string
        """
        buffered = io.BytesIO()
        pil_image.save(buffered, format=format)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    @staticmethod
    def tensor_to_base64(tensor, format: str = "PNG") -> str:
        """
        Convert ComfyUI tensor to base64 string.

        Args:
            tensor: ComfyUI image tensor
            format: Image format

        Returns:
            Base64 encoded string
        """
        pil_image = ImageConverter.tensor_to_pil(tensor)
        return ImageConverter.pil_to_base64(pil_image, format)

    @staticmethod
    def validate_image_for_claude(pil_image: Image.Image) -> Tuple[bool, Optional[str]]:
        """
        Validate image meets Claude's requirements.

        Claude limits:
        - Max size: 5MB
        - Max dimensions: 8000x8000 px (or 2000x2000 with 20+ images)
        - Supported formats: JPEG, PNG, GIF, WebP

        Args:
            pil_image: PIL Image to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check format
        if pil_image.format not in ["JPEG", "PNG", "GIF", "WEBP"]:
            return False, f"Unsupported format: {pil_image.format}. Use JPEG, PNG, GIF, or WebP."

        # Check dimensions
        width, height = pil_image.size
        if width > 8000 or height > 8000:
            return False, f"Image too large: {width}x{height}. Max 8000x8000 px."

        # Check file size (rough estimate)
        buffered = io.BytesIO()
        pil_image.save(buffered, format=pil_image.format or "PNG")
        size_mb = len(buffered.getvalue()) / (1024 * 1024)
        if size_mb > 5:
            return False, f"Image file size too large: {size_mb:.2f}MB. Max 5MB."

        return True, None

    @staticmethod
    def resize_if_needed(pil_image: Image.Image, max_dimension: int = 8000) -> Image.Image:
        """
        Resize image if it exceeds max dimensions while preserving aspect ratio.

        Args:
            pil_image: PIL Image
            max_dimension: Maximum width or height

        Returns:
            Resized PIL Image (or original if no resize needed)
        """
        width, height = pil_image.size

        if width <= max_dimension and height <= max_dimension:
            return pil_image

        # Calculate new dimensions preserving aspect ratio
        if width > height:
            new_width = max_dimension
            new_height = int(height * (max_dimension / width))
        else:
            new_height = max_dimension
            new_width = int(width * (max_dimension / height))

        return pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)


class PromptCache:
    """
    Manages prompt caching for cost optimization.

    Prompt caching can reduce costs by up to 90% for repeated system prompts
    and context that doesn't change between requests.
    """

    def __init__(self):
        """Initialize prompt cache manager."""
        self.cached_prompts: Dict[str, str] = {}

    def get_cached_system_prompt(self, key: str, prompt: str) -> Dict[str, Any]:
        """
        Get a system prompt with cache control.

        Args:
            key: Cache key identifier
            prompt: System prompt text

        Returns:
            System prompt dict with cache control
        """
        return {
            "type": "text",
            "text": prompt,
            "cache_control": {"type": "ephemeral"}
        }

    def build_cached_messages(
        self,
        system: Optional[str],
        messages: List[Dict[str, Any]],
        cache_system: bool = True
    ) -> Tuple[Optional[Dict], List[Dict]]:
        """
        Build messages with appropriate cache control.

        Args:
            system: System prompt
            messages: User/assistant messages
            cache_system: Whether to cache the system prompt

        Returns:
            Tuple of (system_with_cache, messages)
        """
        system_result = None
        if system and cache_system:
            system_result = [self.get_cached_system_prompt("system", system)]
        elif system:
            system_result = system

        return system_result, messages
