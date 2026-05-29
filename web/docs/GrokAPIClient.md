<!-- ABOUTME: Help documentation for the Grok API Client ComfyUI node. -->
<!-- ABOUTME: Initializes a Grok (xAI) API client used by downstream Grok nodes. -->

# Grok API Client

Initializes an xAI Grok API client used by other Grok nodes. The `client` output is a typed `GROK_API_CLIENT` value carrying the resolved API key.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| api_key | String | (empty) | xAI API key (optional). If empty, resolves from ComfyUI Settings > `grok/config.ini` |

## Output

| Output | Type | Description |
|--------|------|-------------|
| client | GROK_API_CLIENT | Typed handle for downstream Grok nodes |

## Notes

- All other Grok nodes accept `client` as optional. Leave it disconnected to let each node resolve the API key from the same chain on its own.
- The Settings UI exposes "ERPK > API Keys > xAI (Grok) API Key" which is read first by the resolution chain.
- Connection failures raise `Grok API key resolution failed: ...` with the resolution-chain message.
