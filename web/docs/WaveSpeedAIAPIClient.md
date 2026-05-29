<!-- ABOUTME: Help documentation for the WaveSpeed Client ComfyUI node. -->
<!-- ABOUTME: Authenticates with the WaveSpeed AI API using a multi-source key resolution chain. -->

# WaveSpeed Client

Creates a client connection to the WaveSpeed AI API. Optional if your API key is configured via ComfyUI Settings or config.ini -- model nodes can run standalone.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| api_key | String | "" | WaveSpeed AI API key (optional). If empty, checks ComfyUI Settings, then config.ini |

## Output

| Output | Type | Description |
|--------|------|-------------|
| client | WAVESPEED_AI_API_CLIENT | API client connection for WaveSpeed nodes |

## Notes

- **Key resolution order:** ComfyUI Settings > node input > config.ini
- Connect the client output to any WaveSpeed model node's `client` input
- If your key is set in ComfyUI Settings, you can skip this node entirely
