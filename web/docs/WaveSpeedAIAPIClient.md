<!-- ABOUTME: Help documentation for the WaveSpeed Client ComfyUI node. -->
<!-- ABOUTME: Authenticates with the WaveSpeed AI API using a multi-source key resolution chain. -->

# WaveSpeed Client

Creates a client connection to the WaveSpeed AI API. Optional if your API key is configured via ComfyUI Settings or config.ini -- model nodes can run standalone.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| api_key | String | "" | WaveSpeed AI API key (optional). A key saved in Settings > ERPK > API Keys stays private and takes priority; with neither, `wavespeed/config.ini` is read. A key typed here is visible to every user of this ComfyUI: it is saved in the workflow, the queue history and image metadata. |

## Output

| Output | Type | Description |
|--------|------|-------------|
| client | WAVESPEED_AI_API_CLIENT | API client connection for WaveSpeed nodes. A preview node shows the key as `ApiKey(set)`. |

## Notes

- **Key resolution order:** ComfyUI Settings > node input > config.ini
- Connect the client output to any WaveSpeed model node's `client` input
- If your key is set in ComfyUI Settings, you can skip this node entirely
