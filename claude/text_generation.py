# ABOUTME: ComfyUI V3 node for general-purpose text generation using Claude models.
# ABOUTME: Supports standard and streaming modes with configurable temperature and tokens.

from comfy_api.latest import IO


class ClaudeTextGeneration(IO.ComfyNode):
    """General-purpose text generation using Claude models."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="ClaudeTextGeneration",
            display_name="Claude Text Generation",
            category="ERPK/Claude",
            description="Generate text using Claude for completion, creative writing, and content generation.",
            not_idempotent=True,
            inputs=[
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip="Text prompt for Claude",
                ),
                IO.Custom("CLAUDE_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip="Claude API client from Claude API Client node (optional if API key is configured in Settings)",
                ),
                IO.String.Input(
                    "system_prompt",
                    multiline=True,
                    default="",
                    optional=True,
                    tooltip="Optional system prompt to guide Claude's behavior",
                ),
                IO.Float.Input(
                    "temperature",
                    default=0.7,
                    min=0.0,
                    max=1.0,
                    step=0.05,
                    optional=True,
                    tooltip="Creativity level (0.0=focused, 1.0=creative)",
                ),
                IO.Int.Input(
                    "max_tokens",
                    default=1024,
                    min=256,
                    max=8192,
                    step=128,
                    optional=True,
                    tooltip="Maximum length of response",
                ),
                IO.Boolean.Input(
                    "use_streaming",
                    default=False,
                    optional=True,
                    tooltip="Enable streaming responses",
                ),
            ],
            outputs=[
                IO.String.Output("response"),
            ],
        )

    @classmethod
    def execute(cls, **kwargs) -> IO.NodeOutput:
        from .claude_api.client import ClaudeClient

        prompt = kwargs.get("prompt", "")
        client = kwargs.get("client")
        system_prompt = kwargs.get("system_prompt", "")
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 1024)
        use_streaming = kwargs.get("use_streaming", False)

        if client is None:
            client = ClaudeClient(api_key=None)

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        try:
            messages = [{"role": "user", "content": prompt.strip()}]
            system = system_prompt.strip() if system_prompt and system_prompt.strip() else None

            if use_streaming and client.enable_streaming:
                response_text = cls._generate_streaming(client, messages, system, temperature, max_tokens)
            else:
                response_text = cls._generate_standard(client, messages, system, temperature, max_tokens)

            print(f"[Claude] Text generated successfully ({len(response_text)} characters)")
            return IO.NodeOutput(response_text)

        except Exception as e:
            error_msg = f"Failed to generate text: {str(e)}"
            print(f"[Claude] Error: {error_msg}")
            raise ValueError(error_msg)

    @classmethod
    def _generate_standard(cls, client, messages, system, temperature, max_tokens):
        """Generate using standard (non-streaming) mode."""
        response = client.send_request(
            messages=messages,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if hasattr(response, 'content') and len(response.content) > 0:
            return response.content[0].text
        else:
            raise ValueError("Invalid response format from Claude API")

    @classmethod
    def _generate_streaming(cls, client, messages, system, temperature, max_tokens):
        """Generate using streaming mode."""
        chunks = []
        for chunk in client.send_request_streaming(
            messages=messages,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            chunks.append(chunk)
        return "".join(chunks)
