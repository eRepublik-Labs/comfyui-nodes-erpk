<!-- ABOUTME: Help documentation for the Qwen Image Max Edit ComfyUI node. -->
<!-- ABOUTME: Premium 20B multi-reference image editing with up to 3 reference images. -->

# Qwen Image Max Edit

Premium multi-reference image editing using the Qwen Image Max 20B model. Accepts up to 3 reference images with a simplified parameter set.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of the desired image modifications |
| images | String | "" | Reference image URLs to edit, max 3, separated by commas or newlines. Ignored when `reference_images` is connected or the grid holds images |
| reference_images | IMAGE | - | Reference images as an IMAGE batch, max 3, one image per slice. Takes precedence over the grid and `images`; sent inline as base64, no upload (optional) |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| width | Int | 1024 | Image width, 256-1536, step 8 (optional) |
| height | Int | 1024 | Image height, 256-1536, step 8 (optional) |
| seed | Int | -1 | Random seed for reproducibility, -1 for random (optional) |
| grid_images | String | `[]` | Hidden. The grid stores its ordered file list here as a JSON array of names in the `input` folder |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Edited image |

## Image grid

With nothing connected to `reference_images`, the node sends the files on its grid. Pick or drop PNG, JPG, or WEBP files, drag a cell to reorder it, and hover a cell and click **×** to remove it. While `reference_images` is connected, the grid dims and the node ignores it.

- Each file goes to the API as its own image, at its own size, in cell order.
- The node applies EXIF orientation, drops any alpha channel, and sends each file as JPEG.
- The grid holds up to 3 files, the model's limit (measured against the endpoint; the WaveSpeed page prose says 6, its schema says 3).
- The grid wins over `images`, so the node reads the URL text only when the grid is empty.
- When you queue, ComfyUI checks that every grid file exists in the `input` folder, even with `reference_images` connected.
- `Connect an image or add images to the grid, or enter at least one image URL` means `reference_images`, the grid and `images` are all empty.

## Notes

- **Pricing:** $0.07 per image
- **API Docs:** [Qwen Image Max Edit](https://wavespeed.ai/docs/docs-api/wavespeed-ai/qwen-image-max-edit)
- A prompt and at least one image (`reference_images`, the grid, or `images`) are required
- Maximum of 3 reference images, the same as the other Qwen Edit nodes
- Simplified parameter set: no output_format, sync_mode, or base64_output options
