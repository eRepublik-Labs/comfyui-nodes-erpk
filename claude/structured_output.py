# ABOUTME: ComfyUI V3 node that gets schema-constrained JSON from Claude via structured outputs.
# ABOUTME: Uses a single CLAUDE_TOOLS definition's input_schema; returns the JSON plus Claude's thinking summary.

import copy
import json
from comfy_api.latest import IO

from .models import effort_input, effort_kwargs


def strict_object_schema(schema):
    """Return a copy of a JSON Schema with additionalProperties: false on every object.

    Structured outputs reject any object schema that does not set it explicitly
    (400 "For 'object' type, 'additionalProperties' must be explicitly set to
    false"), and ClaudeToolDefinition's default schema leaves it out.
    """
    schema = copy.deepcopy(schema)

    def visit(node):
        if isinstance(node, list):
            for item in node:
                visit(item)
            return
        if not isinstance(node, dict):
            return
        node_type = node.get("type")
        if node_type == "object" or (isinstance(node_type, list) and "object" in node_type):
            if node.get("additionalProperties", False) is not False:
                raise ValueError(
                    "Structured outputs require \"additionalProperties\": false on every object; "
                    "remove it from the tool's parameters_json or set it to false"
                )
            node["additionalProperties"] = False
        for value in node.values():
            visit(value)

    visit(schema)
    return schema


class ClaudeStructuredOutput(IO.ComfyNode):
    """Constrains Claude's answer to a tool definition's JSON Schema."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="ClaudeStructuredOutput",
            display_name="Claude Structured Output",
            category="ERPK/Claude/Tools",
            description="Get JSON from Claude that matches a tool definition's schema (structured outputs).",
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
                    tooltip="Ignored: current Claude models reject temperature (kept so saved workflows load).",
                ),
                IO.Int.Input(
                    "max_tokens",
                    default=4096,
                    min=256,
                    max=128000,
                    step=128,
                    optional=True,
                    tooltip="Maximum tokens for the response. Thinking counts toward this limit. Current Claude models allow up to 128K.",
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=2**31 - 1,
                    control_after_generate="randomize",
                    tooltip="Seed for cache control. Randomizes by default to ensure fresh results each run.",
                ),
                effort_input(),
            ],
            outputs=[
                IO.String.Output("json_output"),
                IO.String.Output("thinking"),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    async def execute(cls, **kwargs) -> IO.NodeOutput:
        prompt = kwargs.get("prompt", "")
        tool = kwargs.get("tool")
        client = kwargs.get("client")
        system_prompt = kwargs.get("system_prompt", "")
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
        schema = strict_object_schema(tool_def["input_schema"])
        purpose = f"The JSON you return is {tool_def['name']}: {tool_def['description']}" if tool_def.get("description") else None
        system = "\n\n".join(part for part in (system_prompt.strip() if system_prompt else "", purpose) if part) or None

        response = await client.send_request(
            messages=[{"role": "user", "content": prompt.strip()}],
            system=system,
            max_tokens=max_tokens,
            output_config={"format": {"type": "json_schema", "schema": schema}},
            **effort_kwargs(kwargs.get("effort")),
        )

        if response.stop_reason == "max_tokens":
            raise ValueError(
                f"Claude's JSON was cut off at max_tokens={max_tokens} (thinking counts toward it); raise max_tokens"
            )

        from .claude_api.client import response_text
        try:
            parsed = json.loads(response_text(response))
        except json.JSONDecodeError as e:
            raise ValueError(f"Claude returned text that is not valid JSON: {e}") from e

        json_output = json.dumps(parsed, indent=2)
        thinking = "\n".join(block.thinking for block in response.content if block.type == "thinking")

        print(f"[Claude] Structured output extracted ({len(json_output)} chars JSON)")

        return IO.NodeOutput(json_output, thinking)
