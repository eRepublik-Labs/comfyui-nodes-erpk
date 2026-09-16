<!-- ABOUTME: Help documentation for the MiniMax H3 Image Edit ComfyUI node. -->
<!-- ABOUTME: Re-renders a subject from up to nine reference images per a text instruction. -->

# MiniMax H3 Image Edit

Re-renders the subject of 1 to 9 reference images into a new scene, outfit, pose or art style while preserving identity.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String (multiline) | (empty) | Edit instruction. Cite references as `<Picture 1>` through `<Picture 9>` |
| images | IMAGE | (none) | Reference images as a ComfyUI IMAGE batch, capped at 9. Takes precedence over image_urls (optional) |
| image_urls | String | (empty) | Reference image URL(s), single URL or list, up to 9. Fallback when images is not connected (optional) |
| client | WAVESPEED_AI_API_CLIENT | (none) | WaveSpeed API client (optional if API key is in Settings) |
| aspect_ratio | Combo | auto | Output aspect ratio. auto follows the first reference image (optional) |
| resolution | Combo | 1k | 1k or 2k (optional) |
| output_format | Combo | jpeg | jpeg, png or webp (optional) |
| seed | Int | -1 | Generation seed, sent to the API (optional) |
| loras | MINIMAX_H3_LORAS | (none) | LoRA stack from the MiniMax H3 LoRA Stack node. When connected the call goes to the -lora twin (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | The edited image as a ComfyUI IMAGE tensor |

## Cite references by tag

The instruction should name each reference by its bracket tag, for example:

```
Put the person from <Picture 1> in the jacket from <Picture 2>, standing on a rainy street at night.
```

## Cost

About $0.03 per image at 1k and $0.09 at 2k, plus about $0.005 for each reference beyond the first. With a LoRA stack connected the -lora twin adds a flat $0.015 per image.

## Notes

- At least one reference is required, as an IMAGE batch or a URL
- IMAGE batches are sent as base64 data URIs; URLs are sent as-is
