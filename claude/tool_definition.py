# ABOUTME: ComfyUI V3 node for building Anthropic tool definitions visually.
# ABOUTME: Produces chainable CLAUDE_TOOLS lists for use with structured output or agentic nodes.

import json
from comfy_api.latest import IO


class ClaudeToolDefinition(IO.ComfyNode):
    """Builds an Anthropic tool definition and appends it to an optional chain."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="ClaudeToolDefinition",
            display_name="Claude Tool Definition",
            category="ERPK/Claude/Tools",
            description="Build an Anthropic tool definition visually and chain them together.",
            inputs=[
                IO.String.Input(
                    "tool_name",
                    default="",
                    tooltip="snake_case tool identifier (e.g. extract_person)",
                ),
                IO.String.Input(
                    "description",
                    multiline=True,
                    default="",
                    tooltip="What this tool does — shown to the model",
                ),
                IO.String.Input(
                    "parameters_json",
                    multiline=True,
                    default='{\n  "type": "object",\n  "properties": {},\n  "required": []\n}',
                    tooltip="JSON Schema for the tool's input parameters",
                ),
                IO.Custom("CLAUDE_TOOLS").Input(
                    "previous_tools",
                    optional=True,
                    tooltip="Chain from another Tool Definition node",
                ),
            ],
            outputs=[
                IO.Custom("CLAUDE_TOOLS").Output("tools"),
            ],
        )

    @classmethod
    def execute(cls, **kwargs) -> IO.NodeOutput:
        tool_name = kwargs.get("tool_name", "")
        description = kwargs.get("description", "")
        parameters_json = kwargs.get("parameters_json", "")
        previous_tools = kwargs.get("previous_tools")

        name = tool_name.strip()
        if not name:
            raise ValueError("Tool name cannot be empty")

        try:
            schema = json.loads(parameters_json)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid JSON in parameters_json: {e}")

        if not isinstance(schema, dict) or "type" not in schema:
            raise ValueError("parameters_json must be a JSON object with a 'type' field")

        tool_def = {
            "name": name,
            "description": description,
            "input_schema": schema,
        }

        # Copy previous tools to avoid mutation, then append or replace
        tools = list(previous_tools) if previous_tools else []

        existing_idx = next(
            (i for i, t in enumerate(tools) if t["name"] == name), None
        )
        if existing_idx is not None:
            print(f"[Claude] Warning: duplicate tool name '{name}', replacing previous definition")
            tools[existing_idx] = tool_def
        else:
            tools.append(tool_def)

        return IO.NodeOutput(tools)
