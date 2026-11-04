<!-- ABOUTME: Help documentation for the Qwen Image Edit Plus ComfyUI node. -->
<!-- ABOUTME: Advanced multi-reference image editing with up to 3 reference images. -->

# Qwen Image Edit Plus

Advanced image editing with multiple reference images. Accepts up to 3 reference images and supports bilingual (Chinese and English) text prompts.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| model | Combo | Qwen Edit Plus | Model variant: Qwen Edit Plus or Qwen Edit 2511 (multi-person editing, improved consistency) |
| prompt | String | "" | Text description of the desired image modifications (Chinese or English) |
| images | String | "" | Reference image URLs to edit, max 3, separated by commas or newlines. Ignored when `reference_images` is connected or the grid holds images |
| reference_images | IMAGE | - | Reference images as an IMAGE batch, max 3, one image per slice. Takes precedence over the grid and `images`; sent inline as base64, no upload (optional) |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| width | Int | 1024 | Image width, 256-1536, step 8 (optional) |
| height | Int | 1024 | Image height, 256-1536, step 8 (optional) |
| seed | Int | -1 | Random seed for reproducibility, -1 for random (optional) |
| output_format | Combo | jpeg | Output image format: jpeg, png, webp (optional) |
| enable_sync_mode | Boolean | false | Wait for completion before returning response (optional) |
| enable_base64_output | Boolean | false | Return BASE64-encoded output instead of URL (optional) |
| grid_max_images | Int | 3 | The most images the grid accepts, from 1 to 3 (optional) |
| grid_images | String | `[]` | Hidden. The grid stores its ordered file list here as a JSON array of names in the `input` folder |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Edited image |

## Image grid

With nothing connected to `reference_images`, the node sends the files on its grid. Pick or drop PNG, JPG, or WEBP files, drag a cell to reorder it, and hover a cell and click **×** to remove it. While `reference_images` is connected, the grid dims and the node ignores it.

- Each file goes to the API as its own image, at its own size, in cell order.
- The node applies EXIF orientation, drops any alpha channel, and sends each file as JPEG.
- The grid holds up to 3 files, the model's limit. Lower `grid_max_images` to cap it further.
- The grid wins over `images`, so the node reads the URL text only when the grid is empty.
- When you queue, ComfyUI checks that every grid file exists in the `input` folder, even with `reference_images` connected.
- `Connect an image or add images to the grid, or enter at least one image URL` means `reference_images`, the grid and `images` are all empty.

## Notes

- **Pricing:** $0.02 per image
- **API Docs:** [Qwen Image Edit Plus](https://wavespeed.ai/docs/docs-api/wavespeed-ai/qwen-image-edit-plus)
- A prompt and at least one image (`reference_images`, the grid, or `images`) are required
- Maximum of 3 reference images; provide as comma-separated URLs
- Two model variants: **Qwen Edit Plus** (default) and **Qwen Edit 2511** (multi-person editing, improved consistency)
