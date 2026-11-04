<!-- ABOUTME: Help documentation for the Qwen Image 3.0 Edit ComfyUI node. -->
<!-- ABOUTME: Image editing with up to 3 reference images on Qwen Image 3.0 or 3.0 Pro. -->

# Qwen Image 3.0 Edit

Edits 1 to 3 reference images from a Chinese or English instruction, using Qwen Image 3.0 or Qwen Image 3.0 Pro. Output is 1k or 2k at one of 15 aspect ratios, or at the first reference image's ratio.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| model | Combo | Qwen Image 3.0 | Qwen Image 3.0 or Qwen Image 3.0 Pro |
| prompt | String | "" | Edit instruction in Chinese or English. WaveSpeed recommends at most 800 characters |
| reference_images | IMAGE | - | Reference images as an IMAGE batch, max 3, one image per slice, 384-2048 px per side. Takes precedence over the grid and `reference_images_url`; sent inline as base64, no upload (optional) |
| reference_images_url | String | "" | Reference image URLs, max 3, separated by commas or newlines. Ignored when `reference_images` is connected or the grid holds images (optional) |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| aspect_ratio | Combo | auto | auto (follows the first reference image), 1:1, 1:2, 2:1, 1:3, 3:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 9:21, 21:9 (optional) |
| resolution | Combo | 1k | Output resolution tier: 1k or 2k (optional) |
| enable_prompt_expansion | Boolean | false | Let the model rewrite the instruction into a more detailed prompt (optional) |
| seed | Int | -1 | Generation seed, sent to the API. A fixed seed reproduces the result and lets ComfyUI reuse the cached output; -1 for random (optional) |
| grid_max_images | Int | 3 | The most images the grid accepts, from 1 to 3 (optional) |
| grid_images | String | `[]` | Hidden. The grid stores its ordered file list here as a JSON array of names in the `input` folder |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Edited image |

## Pricing

| Model | 1k | 2k |
|-------|----|----|
| Qwen Image 3.0 | $0.03 | $0.03 |
| Qwen Image 3.0 Pro | $0.04 | $0.075 |

Each reference image adds $0.003.

## Image grid

With nothing connected to `reference_images`, the node sends the files on its grid. Pick or drop PNG, JPG, or WEBP files, drag a cell to reorder it, and hover a cell and click **×** to remove it. While `reference_images` is connected, the grid dims and the node ignores it.

- Each file goes to the API as its own image, at its own size, in cell order.
- The node applies EXIF orientation, drops any alpha channel, and sends each file as JPEG.
- The grid holds up to 3 files, the model's limit. Lower `grid_max_images` to cap it further.
- The grid wins over `reference_images_url`, so the node reads the URL text only when the grid is empty.
- When you queue, ComfyUI checks that every grid file exists in the `input` folder, even with `reference_images` connected.
- `Connect an image or add images to the grid, or enter at least one image URL` means `reference_images`, the grid and `reference_images_url` are all empty.

## Notes

- **API Docs:** [Qwen Image 3.0 Edit](https://wavespeed.ai/docs/docs-api/alibaba/alibaba-qwen-image-3.0-edit), [Qwen Image 3.0 Pro Edit](https://wavespeed.ai/docs/docs-api/alibaba/alibaba-qwen-image-3.0-pro-edit)
- A prompt and at least one image (`reference_images`, the grid, or `reference_images_url`) are required
- More than 3 images is an error, not a silent cut
