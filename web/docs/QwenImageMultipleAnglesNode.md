<!-- ABOUTME: Help documentation for the Qwen Image Multiple Angles ComfyUI node. -->
<!-- ABOUTME: Transforms images by adjusting viewing angle and distance parameters. -->

# Qwen Image Multiple Angles

Transforms reference images by adjusting viewing angle and distance. Supports horizontal rotation, vertical rotation, and distance adjustment with an optional guiding prompt.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| images | String | "" | Reference image URLs to transform, max 3, separated by commas or newlines. Ignored when `reference_images` is connected or the grid holds images |
| reference_images | IMAGE | - | Reference images as an IMAGE batch, max 3, one image per slice. Takes precedence over the grid and `images`; sent inline as base64, no upload (optional) |
| prompt | String | "" | Text description to guide the transformation (optional) |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| horizontal_angle | Int | 0 | Horizontal rotation angle, -90 to 90 degrees (optional) |
| vertical_angle | Int | 0 | Vertical rotation angle, -30 to 60 degrees (optional) |
| distance | Float | 1.0 | Framing, 0.0 to 2.0, sent as the nearest level: 0 close-up, 1 medium, 2 wide; halves round up (optional) |
| width | Int | 1024 | Image width, 256-1536, step 8 (optional) |
| height | Int | 1024 | Image height, 256-1536, step 8 (optional) |
| seed | Int | -1 | Random seed for reproducibility, -1 for random (optional) |
| output_format | Combo | jpeg | Output image format: jpeg, png, webp (optional) |
| enable_sync_mode | Boolean | false | Wait for completion before returning response (optional) |
| enable_base64_output | Boolean | false | Return BASE64-encoded output instead of URL (optional) |
| grid_images | String | `[]` | Hidden. The grid stores its ordered file list here as a JSON array of names in the `input` folder |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Transformed image |

## Image grid

With nothing connected to `reference_images`, the node sends the files on its grid. Pick or drop PNG, JPG, or WEBP files, drag a cell to reorder it, and hover a cell and click **×** to remove it. While `reference_images` is connected, the grid dims and the node ignores it.

- Each file goes to the API as its own image, at its own size, in cell order.
- The node applies EXIF orientation, drops any alpha channel, and sends each file as JPEG.
- The grid holds up to 3 files, the model's limit.
- The grid wins over `images`, so the node reads the URL text only when the grid is empty.
- When you queue, ComfyUI checks that every grid file exists in the `input` folder, even with `reference_images` connected.
- `Connect an image or add images to the grid, or enter at least one image URL` means `reference_images`, the grid and `images` are all empty.

## Notes

- **Pricing:** $0.02 per image
- **API Docs:** [Qwen Image Multiple Angles](https://wavespeed.ai/docs/docs-api/wavespeed-ai/qwen-image-edit-2509-multiple-angles)
- At least 1 reference image is required (up to 3), from `reference_images`, the grid, or `images`
- `images` also accepts the `all_image_urls` list from WaveSpeed Upload Image
- Angle and distance parameters are only sent when they differ from defaults
- Prompt is optional for this node
