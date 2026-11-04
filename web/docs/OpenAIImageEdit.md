<!-- ABOUTME: Help documentation for the OpenAI Image Edit ComfyUI node. -->
<!-- ABOUTME: Edits existing images using OpenAI's image editing API with optional masking. -->

# OpenAI Image Edit

Edits existing images based on text prompts using OpenAI's image editing API. Supports optional masking for targeted inpainting. Connect an image, or pick or drop image files onto the grid on the node.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | Image | — | Input image to edit (optional). When connected, the node sends it and ignores the grid |
| prompt | String | (empty) | Description of how to modify the image |
| client | OPENAI_API_CLIENT | — | OpenAI API client (optional if API key is configured in Settings) |
| mask | Mask | — | Areas to edit: white=edit, black=keep (optional). Enables inpainting |
| model | Combo | gpt-image-2.5-sunburst | Editing model: gpt-image-2.5-sunburst, gpt-image-2.5-flare, gpt-image-2 (optional) |
| size | Combo | 1024x1024 | Output size preset or Custom (optional). Presets: auto, 1024x1024, 1024x1536, 1536x1024, 2048x2048, 2048x1152, 1152x2048, 3840x2160, 2160x3840. Every model accepts any Custom size with edges divisible by 16, aspect ratio 1:3 to 3:1, 655,360 to 8,294,400 pixels, max edge 3840. Above 2560x1440 is experimental per OpenAI |
| custom_width | Int | 1024 | Width when size is Custom (optional). 256 to 3840, step 16 |
| custom_height | Int | 1024 | Height when size is Custom (optional). 256 to 3840, step 16 |
| quality | Combo | auto | Image quality: auto, low, medium, high, xhigh, max (optional). xhigh/max on GPT Image 2.5 only (clamped to high on gpt-image-2) |
| moderation | Combo | auto | Content filter strictness: auto or low (optional). See Notes |
| n | Int | 1 | Number of images to generate (optional). Range: 1–10 |
| background | Combo | auto | auto, transparent, opaque (optional). Transparent works on GPT Image 2.5 only and needs png or webp output; gpt-image-2, or transparent with jpeg, is refused before the call |
| input_fidelity | Combo | auto | auto, high, low (optional). Ignored by every current model: gpt-image-2 and the 2.5 models always edit at high fidelity and reject the field, so it is never sent. Kept so saved workflows load |
| seed | Int | -1 | Cache control only, not sent to the API. -1 randomizes (re-runs every queue); a fixed value reuses the cached result |
| output_format | Combo | png | Output file format: png, jpeg, webp (optional). `transparent` background needs png or webp |
| output_compression | Int | 100 | Compression 0–100 (optional). Sent only with jpeg or webp; png sends neither field |
| grid_max_images | Int | 16 | The most images the grid accepts, from 1 to 16. The selected model's limit also applies (optional) |
| grid_images | String | `[]` | Hidden. The grid stores its ordered file list here as a JSON array of names in the `input` folder |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | Image | Edited image tensor |

## Image grid

With nothing connected to `image`, the node sends the files on its grid instead. While `image` is connected, the grid dims, shows `Image socket connected, grid ignored`, and takes no new files, but keeps the files it has. The grid works as on the Image Grid Loader node: pick or drop PNG, JPG, or WEBP files, drag a cell to reorder it, and hover a cell and click **×** to remove it. The number on each cell is the image's position in the request.

- Each file goes to the API as its own image, at its own size, in cell order. The node does not batch or letterbox them.
- The grid holds no more images than the smaller of `grid_max_images` and the selected model's limit. OpenAI documents one limit for every GPT Image model, so gpt-image-2.5-sunburst, gpt-image-2.5-flare, and gpt-image-2 each take up to 16 images.
- The node applies EXIF orientation, drops any alpha channel, and sends each file as PNG.
- A mask applies to the first image and must have that image's height and width.
- When you queue, ComfyUI checks that every grid file exists in the `input` folder, even with `image` connected. Clear the grid if it names a missing file.

Grid errors name what is at fault:

- `Connect an image or add images to the grid`: `image` is not connected and the grid is empty.
- `grid_images entry 2 not found in ComfyUI's input directory: 'cat.png'`: the file no longer exists under that name in `input`.
- `grid_images entry 1 is outside ComfyUI's input directory: '../cat.png'`: the entry leaves the `input` folder.
- `The grid holds 12 images but grid_max_images is 10; remove 2 or raise grid_max_images`: you lowered `grid_max_images` below the number of images in the grid.
- `The grid holds 17 images but gpt-image-2 takes up to 16; remove 1`: the grid holds more images than the selected model takes.

## Notes

- **`moderation` is a request, not a guarantee**: `low` asks OpenAI for less restrictive filtering. Measured on 2026-09-17, both GPT Image 2.5 models honour it for artistic nudity while gpt-image-2 does not, and gpt-image-2.5-sunburst was inconsistent across identical requests. Graphic violence is refused at both levels on every model. OpenAI documents no per-model difference, so this can change without notice.
- **Refusals are legible**: a blocked request reports whether the prompt or the generated image was refused, plus the categories involved. A prompt-stage refusal is often fixable by rewording; an output-stage one usually is not.
- **System instructions do not apply**: the images endpoint accepts only a prompt, with no system or instructions field. Connecting an OpenAI System Instruction node upstream has no effect here; fold that guidance into the prompt. The OpenAI Image via Responses node is the one image path that does honour it.
- **Sizes were measured live on 2026-09-21**: 512x512 and 256x256 are rejected by every model this node offers, `auto` works everywhere, and 1536x864 works on gpt-image-2 and the 2.5 models. Sizes outside the gpt-image-2 envelope are rejected before the request is sent.
- gpt-image-1.5, gpt-image-1 and gpt-image-1-mini were removed on 2026-10-01. A saved workflow that names one fails validation until a current model is picked
- **Workflows saved before custom_width / custom_height existed load unchanged**: a typed size that is not a preset is restored as Custom with the dimensions filled in.
- Without a mask, the model edits the entire image based on the prompt
- With a mask, only white areas are modified (inpainting mode)
- The mask is converted to an alpha channel internally — white regions become transparent for the API
