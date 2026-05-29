<!-- ABOUTME: Help documentation for the OpenAI API Config ComfyUI node. -->
<!-- ABOUTME: Initializes an OpenAI API client for use by other nodes. -->

# OpenAI API Config

Initializes an OpenAI API client for use by other nodes. Optional if your API key is configured in ComfyUI Settings — generation nodes can create their own client automatically.

## Parameters

This node takes no parameters.

## Output

| Output | Type | Description |
|--------|------|-------------|
| client | OPENAI_API_CLIENT | Configured OpenAI API client instance |

## Notes

- API key resolution order: ComfyUI Settings > node input > config.ini
- This node is optional — text and image nodes can create their own client if an API key is available
