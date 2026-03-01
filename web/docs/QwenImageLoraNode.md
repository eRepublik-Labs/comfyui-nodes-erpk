<!-- ABOUTME: Help documentation for the Qwen Image LoRA ComfyUI node. -->
<!-- ABOUTME: Text-to-image generation guided by up to 3 LoRA models with configurable scales. -->

# Qwen Image LoRA

Generates images from text prompts with up to 3 LoRA model influences. Each LoRA accepts a URL path and a scale factor for fine-grained style control.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| model | Combo | Qwen Image | Model variant: Qwen Image (20B MMDiT) or Qwen Image 2512 (7B, better text rendering) |
| prompt | String | "" | Text description of the image to generate (Chinese or English) |
| lora_1_path | String | - | URL to first LoRA model file (required) |
| lora_1_scale | Float | 1.0 | Scale factor for first LoRA, 0.0-4.0 |
| lora_2_path | String | "" | URL to second LoRA model file (optional) |
| lora_2_scale | Float | 1.0 | Scale factor for second LoRA, 0.0-4.0 (optional) |
| lora_3_path | String | "" | URL to third LoRA model file (optional) |
| lora_3_scale | Float | 1.0 | Scale factor for third LoRA, 0.0-4.0 (optional) |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| width | Int | 1024 | Image width, 256-1536, step 8 (optional) |
| height | Int | 1024 | Image height, 256-1536, step 8 (optional) |
| seed | Int | -1 | Random seed for reproducibility, -1 for random (optional) |
| output_format | Combo | jpeg | Output image format: jpeg, png, webp (optional) |
| enable_sync_mode | Boolean | false | Wait for completion before returning response (optional) |
| enable_base64_output | Boolean | false | Return BASE64-encoded output instead of URL (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Generated image |

## Notes

- **Pricing:** $0.02 per image
- **API Docs:** [Qwen Image LoRA](https://wavespeed.ai/docs/docs-api/wavespeed-ai/qwen-image-text-to-image-lora)
- At least one LoRA path is required; up to 3 LoRAs supported
- Each LoRA scale ranges from 0.0 (no influence) to 4.0 (maximum influence)
- Two model variants: **Qwen Image** (20B MMDiT, default) and **Qwen Image 2512** (7B, better text rendering)
