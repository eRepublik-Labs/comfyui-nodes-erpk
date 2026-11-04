<!-- ABOUTME: Help documentation for the Bytedance Seedream V5.0 Lite Edit ComfyUI node. -->
<!-- ABOUTME: Edits images at higher minimum resolution with enhanced typography. -->

# Bytedance Seedream V5.0 Lite Edit

Edits images at higher minimum resolution (1440px) with enhanced typography using ByteDance's Seedream V5.0 Lite Edit model. Accepts up to 10 reference images.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of the desired image modifications |
| image_url | String | (empty) | Image URL(s) to edit, one per line or comma separated, up to 10. Needed unless images is connected or the grid holds images |
| images | Image | -- | Images to edit as an IMAGE batch, one image per slice, up to 10 (optional). Sent inline as base64, no upload. Takes precedence over the grid and image_url. Batched images must share one size, so combine different sizes on the grid or through URLs |
| size_preset | Combo | "Custom" | Resolution preset. Select "Custom" to use manual width/height |
| client | WAVESPEED_AI_API_CLIENT | -- | WaveSpeed API client (optional if API key is configured in Settings) |
| width | Int | 2048 | Custom width in pixels, 1440-4096, step 8 (optional) |
| height | Int | 2048 | Custom height in pixels, 1440-4096, step 8 (optional) |
| show_aspect_ratio | Boolean | true | Show aspect ratio in node title (optional) |
| enable_sync_mode | Boolean | false | Wait for result before returning response (optional) |
| enable_base64_output | Boolean | false | Return BASE64 encoded output instead of URLs (optional) |
| grid_max_images | Int | 10 | The most images the grid accepts, from 1 to 10 (optional) |
| grid_images | String | `[]` | Hidden. The grid stores its ordered file list here as a JSON array of names in the `input` folder |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Edited image |

## Image grid

With nothing connected to `images`, the node sends the files on its grid. Pick or drop PNG, JPG, or WEBP files, drag a cell to reorder it, and hover a cell and click **×** to remove it. While `images` is connected, the grid dims and the node ignores it.

- Each file goes to the API as its own image, at its own size, in cell order.
- The node applies EXIF orientation, drops any alpha channel, and sends each file as JPEG.
- The grid holds up to 10 files, the model's limit. Lower `grid_max_images` to cap it further.
- The grid wins over `image_url`, so the node reads the URL text only when the grid is empty.
- When you queue, ComfyUI checks that every grid file exists in the `input` folder, even with `images` connected.
- `Connect an image or add images to the grid, or enter at least one image URL` means `images`, the grid and `image_url` are all empty.

## Notes

- **Pricing:** $0.035/image
- **API Docs:** [Bytedance Seedream V5.0 Lite Edit](https://wavespeed.ai/docs/docs-api/bytedance/bytedance-seedream-v5-0-lite-edit)
- Use the **WaveSpeed Upload Image** node to get image URLs from local images
- Accepts up to 10 reference images
