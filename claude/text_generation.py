"""
Claude Text Generation Node

General-purpose text generation using Claude models.
"""

from .claude_api.client import ClaudeClient


class ClaudeTextGeneration:
    """
    Claude Text Generation Node

    General-purpose text generation for various tasks including:
    - Text completion and expansion
    - Creative writing
    - Text transformation
    - Content generation
    - And more
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": (
                    "CLAUDE_API_CLIENT",
                    {"tooltip": "Claude API client from Claude API Client node"}
                ),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Text prompt for Claude"
                    }
                ),
            },
            "optional": {
                "system_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Optional system prompt to guide Claude's behavior"
                    }
                ),
                "temperature": (
                    "FLOAT",
                    {
                        "default": 0.7,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.05,
                        "tooltip": "Creativity level (0.0=focused, 1.0=creative)"
                    }
                ),
                "max_tokens": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 256,
                        "max": 8192,
                        "step": 128,
                        "tooltip": "Maximum length of response"
                    }
                ),
                "use_streaming": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Enable streaming responses"
                    }
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "generate"
    CATEGORY = "ERPK/Claude"

    def generate(
        self,
        client: ClaudeClient,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        use_streaming: bool = False
    ):
        """
        Generate text using Claude.

        Args:
            client: Claude API client
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Creativity level
            max_tokens: Max output tokens
            use_streaming: Enable streaming

        Returns:
            Tuple containing generated text
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        try:
            # Build messages
            messages = [
                {"role": "user", "content": prompt.strip()}
            ]

            # Prepare system prompt (use None if empty)
            system = system_prompt.strip() if system_prompt and system_prompt.strip() else None

            # Send request (streaming or standard)
            if use_streaming and client.enable_streaming:
                response_text = self._generate_streaming(client, messages, system, temperature, max_tokens)
            else:
                response_text = self._generate_standard(client, messages, system, temperature, max_tokens)

            print(f"[Claude] Text generated successfully ({len(response_text)} characters)")

            return (response_text,)

        except Exception as e:
            error_msg = f"Failed to generate text: {str(e)}"
            print(f"[Claude] Error: {error_msg}")
            raise ValueError(error_msg)

    def _generate_standard(
        self,
        client: ClaudeClient,
        messages: list,
        system: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate using standard (non-streaming) mode."""
        response = client.send_request(
            messages=messages,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens
        )

        if hasattr(response, 'content') and len(response.content) > 0:
            return response.content[0].text
        else:
            raise ValueError("Invalid response format from Claude API")

    def _generate_streaming(
        self,
        client: ClaudeClient,
        messages: list,
        system: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate using streaming mode."""
        chunks = []
        for chunk in client.send_request_streaming(
            messages=messages,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens
        ):
            chunks.append(chunk)

        return "".join(chunks)


# Node registration
NODE_CLASS_MAPPINGS = {
    "ClaudeTextGeneration": ClaudeTextGeneration,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ClaudeTextGeneration": "Claude Text Generation",
}
