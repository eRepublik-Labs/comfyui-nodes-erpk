<!-- ABOUTME: Help documentation for the Gemini API Config ComfyUI node. -->
<!-- ABOUTME: Initializes a Gemini API client for use by other Gemini nodes. -->

# Gemini API Config

Initializes a Gemini API client for use by other Gemini nodes. Optional — Gemini nodes work without this node as long as your API key is configured in Settings, the `GOOGLE_API_KEY` environment variable, or config.ini.

## Parameters

This node takes no parameters.

## Output

| Output | Type | Description |
|--------|------|-------------|
| client | GEMINI_API_CLIENT | Configured Gemini API client instance |

## Notes

- API key is resolved in priority order: ComfyUI Settings > environment variable > config.ini
- Other Gemini nodes can run without this node if an API key is configured in Settings or environment
- Connect the client output to System Instruction or Safety Settings nodes before passing to generation nodes
