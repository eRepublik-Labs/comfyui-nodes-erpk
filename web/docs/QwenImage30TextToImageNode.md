<!-- ABOUTME: Help documentation for the Qwen Image 3.0 Text-to-Image ComfyUI node. -->
<!-- ABOUTME: Text-to-image generation on Qwen Image 3.0 or 3.0 Pro at 1k or 2k. -->

# Qwen Image 3.0 Text-to-Image

Generates an image from a Chinese or English prompt using Qwen Image 3.0 or Qwen Image 3.0 Pro, at one of 15 aspect ratios and a 1k or 2k resolution tier.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| model | Combo | Qwen Image 3.0 | Qwen Image 3.0 or Qwen Image 3.0 Pro |
| prompt | String | "" | Image description in Chinese or English. WaveSpeed recommends at most 800 characters |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| aspect_ratio | Combo | 1:1 | 1:1, 1:2, 2:1, 1:3, 3:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 9:21, 21:9 (optional) |
| resolution | Combo | 1k | Output resolution tier: 1k or 2k (optional) |
| enable_prompt_expansion | Boolean | false | Let the model rewrite the prompt into a more detailed one (optional) |
| seed | Int | -1 | Generation seed, sent to the API. A fixed seed reproduces the result and lets ComfyUI reuse the cached output; -1 for random (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Generated image |

## Pricing

| Model | 1k | 2k |
|-------|----|----|
| Qwen Image 3.0 | $0.03 | $0.03 |
| Qwen Image 3.0 Pro | $0.04 | $0.075 |

## Notes

- **API Docs:** [Qwen Image 3.0 Text-to-Image](https://wavespeed.ai/docs/docs-api/alibaba/alibaba-qwen-image-3.0-text-to-image), [Qwen Image 3.0 Pro Text-to-Image](https://wavespeed.ai/docs/docs-api/alibaba/alibaba-qwen-image-3.0-pro-text-to-image)
