# ABOUTME: ComfyUI node that uses forced tool use to get guaranteed structured JSON from Claude.
# ABOUTME: Accepts a single CLAUDE_TOOLS definition and returns the extracted JSON plus any thinking text.

import json


class ClaudeStructuredOutput:
    """Forces Claude to respond with structured JSON via the tool use API."""

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
                        "tooltip": "Prompt describing what to extract or generate"
                    }
                ),
                "tool": (
                    "CLAUDE_TOOLS",
                    {"tooltip": "Tool definition (must contain exactly 1 tool)"}
                ),
            },
            "optional": {
                "system_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Optional system prompt to guide extraction behavior"
                    }
                ),
                "temperature": (
                    "FLOAT",
                    {
                        "default": 0.0,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.05,
                        "tooltip": "Low values for consistent output (0.0 recommended)"
                    }
                ),
                "max_tokens": (
                    "INT",
                    {
                        "default": 4096,
                        "min": 256,
                        "max": 8192,
                        "step": 128,
                        "tooltip": "Maximum tokens for the response"
                    }
                ),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("json_output", "thinking")
    FUNCTION = "extract"
    CATEGORY = "ERPK/Claude/Tools"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    def extract(
        self,
        client,
        prompt,
        tool,
        system_prompt="",
        temperature=0.0,
        max_tokens=4096,
    ):
        """Call Claude with forced tool use and extract the structured JSON result."""
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

        return (json_output, thinking)


NODE_CLASS_MAPPINGS = {
    "ClaudeStructuredOutput": ClaudeStructuredOutput,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ClaudeStructuredOutput": "Claude Structured Output",
}
