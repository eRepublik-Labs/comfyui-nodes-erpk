# ABOUTME: ComfyUI node for building Anthropic tool definitions visually.
# ABOUTME: Produces chainable CLAUDE_TOOLS lists for use with structured output or agentic nodes.

import json


class ClaudeToolDefinition:
    """Builds an Anthropic tool definition and appends it to an optional chain."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "tool_name": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "snake_case tool identifier (e.g. extract_person)"
                    }
                ),
                "description": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "What this tool does — shown to the model"
                    }
                ),
                "parameters_json": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": '{\n  "type": "object",\n  "properties": {},\n  "required": []\n}',
                        "tooltip": "JSON Schema for the tool's input parameters"
                    }
                ),
            },
            "optional": {
                "previous_tools": (
                    "CLAUDE_TOOLS",
                    {
                        "tooltip": "Chain from another Tool Definition node"
                    }
                ),
            }
        }

    RETURN_TYPES = ("CLAUDE_TOOLS",)
    RETURN_NAMES = ("tools",)
    FUNCTION = "build_tool"
    CATEGORY = "ERPK/Claude/Tools"

    def build_tool(self, tool_name, description, parameters_json, previous_tools=None):
        """Validate inputs, build a tool dict, and append to the chain."""
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

        return (tools,)


NODE_CLASS_MAPPINGS = {
    "ClaudeToolDefinition": ClaudeToolDefinition,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ClaudeToolDefinition": "Claude Tool Definition",
}
