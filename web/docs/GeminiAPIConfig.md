<!-- ABOUTME: Help documentation for the Gemini API Config ComfyUI node. -->
<!-- ABOUTME: Initializes a Gemini API client for use by other Gemini nodes. -->

# Gemini API Config

Initializes a Gemini API client for use by other Gemini nodes. Optional if your API key is configured via ComfyUI Settings, environment variable, or config.ini.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| api_key | String | "" | Google API key (optional). If empty, uses Settings, GOOGLE_API_KEY env var, or config.ini. |

## Output

| Output | Type | Description |
|--------|------|-------------|
| client | GEMINI_API_CLIENT | Configured Gemini API client instance |

## Notes

- API key is resolved in priority order: ComfyUI Settings > widget > environment variable > config.ini
- Other Gemini nodes can run without this node if an API key is configured in Settings or environment
- Connect the client output to System Instruction or Safety Settings nodes before passing to generation nodes
