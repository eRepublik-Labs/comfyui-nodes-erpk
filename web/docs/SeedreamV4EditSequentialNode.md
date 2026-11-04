<!-- ABOUTME: Help documentation for the Bytedance Seedream V4 Edit Sequential ComfyUI node. -->
<!-- ABOUTME: Edits images with sequential generation for multiple coherent results. -->

# Bytedance Seedream V4 Edit Sequential

Edits images with sequential generation for multiple coherent results using ByteDance's Seedream V4 Edit Sequential model.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of desired modifications. The node automatically appends the image count |
| max_images | Int | 4 | Number of images to generate (1-15) |
| size_preset | Combo | "Custom" | Resolution preset. Select "Custom" to use manual width/height |
| client | WAVESPEED_AI_API_CLIENT | -- | WaveSpeed API client (optional if API key is configured in Settings) |
| image_url | String | (empty) | Image URL(s) to edit, one per line or comma separated, up to 10. Ignored when images is connected or the grid holds images (optional) |
| images | Image | -- | Images to edit as an IMAGE batch, one image per slice, up to 10 (optional). Sent inline as base64, no upload. Takes precedence over the grid and image_url. Batched images must share one size, so combine different sizes on the grid or through URLs |
| width | Int | 1408 | Custom width in pixels, 320-4096, step 8 (optional) |
| height | Int | 1408 | Custom height in pixels, 320-4096, step 8 (optional) |
| show_aspect_ratio | Boolean | true | Show aspect ratio in node title (optional) |
| enable_sync_mode | Boolean | false | Wait for result before returning response (optional) |
| enable_base64_output | Boolean | false | Return BASE64 encoded output instead of URLs (optional) |
| grid_images | String | `[]` | Hidden. The grid stores its ordered file list here as a JSON array of names in the `input` folder |

## Output

| Output | Type | Description |
|--------|------|-------------|
| images | IMAGE | Batch of edited images |

## Image grid

With nothing connected to `images`, the node sends the files on its grid. Pick or drop PNG, JPG, or WEBP files, drag a cell to reorder it, and hover a cell and click **×** to remove it. While `images` is connected, the grid dims and the node ignores it.

- Each file goes to the API as its own image, at its own size, in cell order.
- The node applies EXIF orientation, drops any alpha channel, and sends each file as JPEG.
- The grid holds up to 10 files, the model's limit.
- The grid wins over `image_url`, so the node reads the URL text only when the grid is empty.
- When you queue, ComfyUI checks that every grid file exists in the `input` folder, even with `images` connected.
- With `images`, the grid and `image_url` all empty, the node edits from the prompt alone.

## Notes

- **Pricing:** $0.027/image
- **API Docs:** [Bytedance Seedream V4 Edit Sequential](https://wavespeed.ai/docs/docs-api/bytedance/bytedance-seedream-v4-edit-sequential)
- Reference images are optional -- works as text-to-image when no images are provided
- The node automatically appends "Generate a set of N consecutive." to your prompt
