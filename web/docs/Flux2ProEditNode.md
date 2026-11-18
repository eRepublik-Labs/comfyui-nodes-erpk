<!-- ABOUTME: Help documentation for the FLUX.2 Pro Edit ComfyUI node. -->
<!-- ABOUTME: Edits from up to 3 images, with an optional output size and a seed sent to the API. -->

# FLUX.2 Pro Edit

Edits images from a text prompt with FLUX.2 Pro, using up to 3 input images.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of the desired modifications |
| images | Image | -- | Images to edit as an IMAGE batch, one image per slice, up to 3 (optional). Sent inline as base64, no upload. Takes precedence over the grid and image_url. Batched images must share one size, so combine different sizes on the grid or through URLs |
| image_url | String | (empty) | Image URL(s) to edit, one per line or comma separated, up to 3. Needed unless images is connected or the grid holds images |
| width | Int | 0 | Output width, 256 to 2048. Leave width and height at 0 to let the API choose the size |
| height | Int | 0 | Output height, 256 to 2048. Leave width and height at 0 to let the API choose the size |
| client | WAVESPEED_AI_API_CLIENT | -- | WaveSpeed API client (optional if API key is configured in Settings) |
| seed | Int | -1 | Sent to the API. -1 picks a random seed and generates again every run; a fixed value reuses the cached result |
| grid_images | String | `[]` | Hidden. The grid stores its ordered file list here as a JSON array of names in the `input` folder |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Edited image |

## Image grid

With nothing connected to `images`, the node sends the files on its grid. Pick or drop PNG, JPG, or WebP files, drag a cell to reorder it, click a cell to see the image full size, and hover a cell and click **×** to remove it. Click **Reference images** at the top of the grid to collapse it to its header, which still shows the count, and click it again to expand it. While `images` is connected, the grid dims and the node ignores it.

- Each file goes to the API as its own image, at its own size, in cell order.
- The node applies EXIF orientation, drops any alpha channel, and sends each file as JPEG.
- The grid holds up to 3 files, the model's limit.
- The grid wins over `image_url`, so the node reads the URL text only when the grid is empty.
- When you queue, ComfyUI checks that every grid file exists in the `input` folder, even with `images` connected.
- `Connect an image or add images to the grid, or enter at least one image URL` means `images`, the grid and `image_url` are all empty.

## Notes

- **Pricing:** $0.06 per image
- **API Docs:** [FLUX.2 Pro Edit](https://wavespeed.ai/docs/docs-api/wavespeed-ai/flux-2-pro-edit)
- Setting only one of width and height, or a value outside 256 to 2048, is an error that names both values
- More than 3 input images is an error that names the count; nothing is dropped silently
