Browse Models

# API Integration

WaveSpeed AI exposes a unified REST endpoint at `/api/v3/{model_uuid}` for submitting tasks, checking status, and retrieving results. Add `Authorization: Bearer <YOUR_API_KEY>` and `Content-Type: application/json` headers to every request.

## Example Usage [Permalink for this section](https://wavespeed.ai/docs/docs-api\#example-usage)

cURLPythonJavaScript

```bash

curl --location --request POST "https://api.wavespeed.ai/api/v3/wavespeed-ai/flux-dev-lora" \
--header "Authorization: Bearer $WAVESPEED_API_KEY" \
--header "Content-Type: application/json" \
--data-raw '{
  "prompt": "Octopus vs crab chess game, underwater, vibrant colors",
  "loras": [{\
    "path": "nerijs/pixel-art-xl",\
    "scale": 0.8\
  }],
  "output_format": "png"
}'
```

[How to Use Sync Mode](https://wavespeed.ai/docs/sync-mode "How to Use Sync Mode") [Pixverse Lipsync](https://wavespeed.ai/docs/docs-api/pixverse/pixverse-lipsync "Pixverse Lipsync")

Chatwoot

We are away at the moment

Typically replies in a few minutes

Start Conversation

[![Chatwoot](https://app.chatwoot.com/brand-assets/logo_thumbnail.svg)Powered by Chatwoot](https://www.chatwoot.com/?utm_medium=survey&utm_campaign=branding)
