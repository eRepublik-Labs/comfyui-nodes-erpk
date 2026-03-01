<!-- ABOUTME: Help documentation for the Qwen Image Edit Plus LoRA ComfyUI node. -->
<!-- ABOUTME: Multi-reference image editing guided by up to 3 LoRA models with configurable scales. -->

# Qwen Image Edit Plus LoRA

Advanced image editing with multiple reference images and up to 3 LoRA model influences. Supports two model variants for different editing capabilities.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| model | Combo | Qwen Edit Plus LoRA | Model variant: Qwen Edit Plus LoRA or Qwen Edit 2511 LoRA (multi-person editing, improved consistency) |
| prompt | String | "" | Text description of the desired image modifications (Chinese or English) |
| images | String | - | Reference images to edit, max 3 (comma-separated URLs or paths) |
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
| image | IMAGE | Edited image |

## Notes

- **Pricing:** $0.02 per image
- **API Docs:** [Qwen Image Edit Plus LoRA](https://wavespeed.ai/docs/docs-api/wavespeed-ai/qwen-image-edit-plus-lora)
- Prompt, images, and at least one LoRA path are all required
- Maximum of 3 reference images and 3 LoRAs supported
- Two model variants: **Qwen Edit Plus LoRA** (default) and **Qwen Edit 2511 LoRA** (multi-person editing, improved consistency)
