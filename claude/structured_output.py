# ABOUTME: ComfyUI V3 node that uses forced tool use to get guaranteed structured JSON from Claude.
# ABOUTME: Accepts a single CLAUDE_TOOLS definition and returns the extracted JSON plus any thinking text.

import json
from comfy_api.latest import IO


class ClaudeStructuredOutput(IO.ComfyNode):
    """Forces Claude to respond with structured JSON via the tool use API."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="ClaudeStructuredOutput",
            display_name="Claude Structured Output",
            category="ERPK/Claude/Tools",
            description="Force Claude to respond with structured JSON via tool use.",
            not_idempotent=True,
            inputs=[
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip="Prompt describing what to extract or generate",
                ),
                IO.Custom("CLAUDE_TOOLS").Input(
                    "tool",
                    tooltip="Tool definition (must contain exactly 1 tool)",
                ),
                IO.Custom("CLAUDE_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip="Claude API client (optional if API key is configured in Settings)",
                ),
                IO.String.Input(
                    "system_prompt",
                    multiline=True,
                    default="",
                    optional=True,
                    tooltip="Optional system prompt to guide extraction behavior",
                ),
                IO.Float.Input(
                    "temperature",
                    default=0.0,
                    min=0.0,
                    max=1.0,
                    step=0.05,
                    optional=True,
                    tooltip="Low values for consistent output (0.0 recommended)",
                ),
                IO.Int.Input(
                    "max_tokens",
                    default=4096,
                    min=256,
                    max=8192,
                    step=128,
                    optional=True,
                    tooltip="Maximum tokens for the response",
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=2**31 - 1,
                    control_after_generate="randomize",
                    tooltip="Seed for cache control. Randomizes by default to ensure fresh results each run.",
                ),
            ],
            outputs=[
                IO.String.Output("json_output"),
                IO.String.Output("thinking"),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        return kwargs.get("seed", -1)

    @classmethod
    def execute(cls, **kwargs) -> IO.NodeOutput:
        prompt = kwargs.get("prompt", "")
        tool = kwargs.get("tool")
        client = kwargs.get("client")
        system_prompt = kwargs.get("system_prompt", "")
        temperature = kwargs.get("temperature", 0.0)
        max_tokens = kwargs.get("max_tokens", 4096)

        if client is None:
            from .claude_api.client import ClaudeClient
            client = ClaudeClient(api_key=None)

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        if len(tool) != 1:
            raise ValueError(
                f"Structured output requires exactly 1 tool definition, got {len(tool)}"
            )

        tool_def = tool[0]
        tool_name = tool_def["name"]

        system = system_prompt.strip() if system_prompt and system_prompt.strip() else None

        response = client.send_request(
            messages=[{"role": "user", "content": prompt.strip()}],
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tool,
            tool_choice={"type": "tool", "name": tool_name},
        )

        # Extract thinking text and tool use result from response content blocks
        thinking_parts = []
        tool_input = None

        for block in response.content:
            if block.type == "text":
                thinking_parts.append(block.text)
            elif block.type == "tool_use":
                tool_input = block.input

        if tool_input is None:
            raise ValueError("No tool_use block found in response")

        json_output = json.dumps(tool_input, indent=2)
        thinking = "\n".join(thinking_parts)

        print(f"[Claude] Structured output extracted ({len(json_output)} chars JSON)")

        return IO.NodeOutput(json_output, thinking)
