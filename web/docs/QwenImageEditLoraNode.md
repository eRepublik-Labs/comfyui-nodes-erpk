<!-- ABOUTME: Help documentation for the Qwen Image Edit LoRA ComfyUI node. -->
<!-- ABOUTME: Single-image editing guided by up to 3 LoRA models with configurable scales. -->

# Qwen Image Edit LoRA

Edits images based on text prompts with up to 3 LoRA model influences. Combines image editing with LoRA-guided style control.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of the desired image modifications (Chinese or English) |
| image | String | - | The image to edit (URL or path) |
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
- **API Docs:** [Qwen Image Edit LoRA](https://wavespeed.ai/docs/docs-api/wavespeed-ai/qwen-image-edit-lora)
- Prompt, image, and at least one LoRA path are all required
- Up to 3 LoRAs supported with individual scale factors (0.0-4.0)
- Use the WaveSpeed Upload Image node to get a URL for local images
