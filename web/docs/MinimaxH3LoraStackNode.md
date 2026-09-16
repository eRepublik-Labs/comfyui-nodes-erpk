<!-- ABOUTME: Help documentation for the MiniMax H3 LoRA Stack ComfyUI node. -->
<!-- ABOUTME: Collects up to three LoRA weights for any MiniMax H3 generation node. -->

# MiniMax H3 LoRA Stack

Collects up to three LoRA weights as `{path, scale}` pairs. Connect the output to the `loras` socket of any MiniMax H3 node and that node calls the endpoint's `-lora` twin.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| lora_1_path | String | (empty) | URL of the first LoRA file (required) |
| lora_1_scale | Float | 1.0 | Scale for the first LoRA. Range: 0.0-4.0 |
| lora_2_path | String | (empty) | URL of the second LoRA file (optional) |
| lora_2_scale | Float | 1.0 | Scale for the second LoRA. Range: 0.0-4.0 (optional) |
| lora_3_path | String | (empty) | URL of the third LoRA file (optional) |
| lora_3_scale | Float | 1.0 | Scale for the third LoRA. Range: 0.0-4.0 (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| loras | MINIMAX_H3_LORAS | List of up to 3 `{path, scale}` entries |

## This is a config node

It calls no API and takes no seed, so ComfyUI caches it like any other input. Only the H3 node it feeds re-runs when a path or scale changes.

## Which nodes accept it

Text-to-Video, Image-to-Video (standard tier only), Reference-to-Video, Text-to-Image and Image Edit. Video Edit and Video Extend have no `-lora` endpoint and no socket. Selecting the Spicy tier on Image-to-Video with a stack connected raises an error.

## Cost

Video `-lora` twins charge a higher per-second rate (about 25% more on text/image-to-video, 20% more on reference-to-video). Image `-lora` twins add a flat $0.015 per image.

## Notes

- WaveSpeed documents the `{path, scale}` shape and the 3-item cap but no range for `scale`; 0.0-4.0 follows this package's Qwen LoRA nodes
- Empty path fields are skipped; at least one path is required
