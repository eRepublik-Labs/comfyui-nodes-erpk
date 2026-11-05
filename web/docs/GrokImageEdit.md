<!-- ABOUTME: Help documentation for the Grok Image Edit ComfyUI node. -->
<!-- ABOUTME: Single or multi-image editing (up to 5 sources) via xAI's grok-imagine-image-2.0. -->

# Grok Image Edit

Edits one or more input images using a text prompt. Pass a batched IMAGE tensor with up to 5 frames for multi-image editing (xAI's documented cap for grok-imagine-image-2.0). Connect an image, or pick or drop image files onto the grid on the node.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | IMAGE | — | Source image(s) (optional). Batched tensor of up to 5 frames (xAI cap); the node rejects a larger batch before the API call. When connected, the node sends it and ignores the grid |
| prompt | String | (empty) | Editing instructions |
| client | GROK_API_CLIENT | — | Grok API client (optional if API key is in Settings) |
| model | Combo | grok-imagine-image-2.0 | Image model. Only option: grok-imagine-image-2.0 (optional) |
| aspect_ratio | Combo | auto | "auto" follows the first source image; otherwise one of 1:1, 16:9, 9:16, 4:3, 3:4, 2:1, 1:2, 3:2, 2:3, 19.5:9, 9:19.5, 20:9, 9:20 (optional) |
| resolution | Combo | auto | auto, 1k (~1024px) or 2k (~2048px). "auto" sends nothing and lets xAI choose (optional) |
| n | Int | 1 | Number of edited variations, 1-10. Each one is billed (optional) |
| quality | Combo | auto | auto, low or medium. "auto" sends nothing; xAI then serves medium for edits. Billed at the quality served (optional) |
| grid_images | String | `[]` | Hidden. The grid stores its ordered file list here as a JSON array of names in the `input` folder |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Edited image tensor (a batch of n images) |

## Image grid

With nothing connected to `image`, the node sends the files on its grid instead. While `image` is connected, the grid dims, shows `Image socket connected, grid ignored`, and takes no new files, but keeps the files it has. The grid works as on the Image Grid Loader node: pick or drop PNG, JPG, or WebP files, drag a cell to reorder it, and hover a cell and click **×** to remove it. Click **Reference images** at the top of the grid to collapse it to its header, which still shows the count, and click it again to expand it. The number on each cell is the image's position in the request: cell 1 is `<IMAGE_0>` in the prompt, cell 2 is `<IMAGE_1>`, and so on.

- Each file goes to xAI as its own source image, in cell order. The node does not batch or letterbox them.
- The grid holds up to 5 files, grok-imagine-image-2.0's limit.
- The node applies EXIF orientation, drops any alpha channel, and sends each file as a JPEG data URI. A file keeps its size unless its longest edge is over 2048 px or the request would pass the xai-sdk's 20 MiB limit; then the node scales it down, as it does a connected image.
- When you queue, ComfyUI checks that every grid file exists in the `input` folder, even with `image` connected. Clear the grid if it names a missing file.

Grid errors name what is at fault:

- `Connect an image or add images to the grid`: `image` is not connected and the grid is empty.
- `grid_images entry 2 not found in ComfyUI's input directory: 'cat.png'`: the file no longer exists under that name in `input`.
- `grid_images entry 1 is outside ComfyUI's input directory: '../cat.png'`: the entry leaves the `input` folder.
- `The grid holds 6 images but grok-imagine-image-2.0 takes up to 5 images; remove 1`: the grid holds more images than the selected model takes.

## Notes

- xAI requires images as `application/json` data URIs (not multipart). This node converts each source image, from the socket or the grid, to a base64 JPEG data URI automatically, downscaling if needed so all sources fit one request (the xai-sdk sends at most 20 MiB).
- Multi-turn editing: chain Edit nodes by feeding each output into the next Edit's `image` input.
- The first frame of a batch is the primary source; additional frames act as references in the order received. Address them in the prompt as `<IMAGE_0>`, `<IMAGE_1>`, and so on.
- Async-enabled — concurrent Grok Image Edit nodes share the event loop.
