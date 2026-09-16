<!-- ABOUTME: Help documentation for the MiniMax H3 Text-to-Image ComfyUI node. -->
<!-- ABOUTME: Generates a 1k or 2k image from a text prompt, optionally with LoRAs. -->

# MiniMax H3 Text-to-Image

Generates a single image from a text prompt at 1k (~1MP) or 2k (~4MP) in one of fifteen aspect ratios.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String (multiline) | (empty) | Text description of the image |
| client | WAVESPEED_AI_API_CLIENT | (none) | WaveSpeed API client (optional if API key is in Settings) |
| aspect_ratio | Combo | 1:1 | 1:1, 1:2, 2:1, 1:3, 3:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 9:21, 21:9 (optional) |
| resolution | Combo | 1k | 1k (~1MP) or 2k (~4MP) (optional) |
| output_format | Combo | jpeg | jpeg, png or webp (optional) |
| seed | Int | -1 | Generation seed, sent to the API (optional) |
| loras | MINIMAX_H3_LORAS | (none) | LoRA stack from the MiniMax H3 LoRA Stack node. When connected the call goes to the -lora twin (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | The generated image as a ComfyUI IMAGE tensor |

## The seed is real

MiniMax H3 accepts a seed and honours it. A fixed seed reproduces the same image and lets ComfyUI reuse the cached result. -1 generates a new one on every queue.

## Cost

About $0.02 per image at 1k and $0.06 at 2k. With a LoRA stack connected the -lora twin adds a flat $0.015 per image.

## Notes

- Output is shown inline on the node and returned as an IMAGE tensor
- This is the open-weights edition of MiniMax H3 hosted by WaveSpeed, separate from MiniMax's own API
