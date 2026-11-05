<!-- ABOUTME: Help documentation for the OpenAI Image Edit ComfyUI node. -->
<!-- ABOUTME: Edits existing images using OpenAI's image editing API with optional masking. -->

# OpenAI Image Edit

Edits existing images based on text prompts using OpenAI's image editing API. Supports optional masking for targeted inpainting, or a markup layer of drawn marks that shows the model where and what to edit. Connect an image, or pick or drop image files onto the grid on the node.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | Image | — | Input image to edit (optional). When connected, the node sends it and ignores the grid |
| prompt | String | (empty) | Description of how to modify the image |
| client | OPENAI_API_CLIENT | — | OpenAI API client (optional if API key is configured in Settings) |
| mask | Mask | — | Areas to edit: white=edit, black=keep (optional). Enables inpainting |
| markup | Image | — | Markup layer: arrows, circles or text drawn on a transparent layer the size of image 1 (optional). Not with `mask`. See Markup |
| markup_mask | Mask | — | The MASK of the Load Image that loads the markup, white where the layer is transparent (optional). Needs `markup` |
| model | Combo | gpt-image-2.6-sunburst | Editing model: gpt-image-2.6-sunburst, gpt-image-2.6-flare, gpt-image-2.5-sunburst, gpt-image-2.5-flare, gpt-image-2 (optional) |
| size | Combo | 1024x1024 | Output size preset or Custom (optional). Presets: auto, 1024x1024, 1024x1536, 1536x1024, 2048x2048, 2048x1152, 1152x2048, 3840x2160, 2160x3840. Every model accepts any Custom size with edges divisible by 16, aspect ratio 1:3 to 3:1, 655,360 to 8,294,400 pixels, max edge 3840. Above 2560x1440 is experimental per OpenAI |
| custom_width | Int | 1024 | Width when size is Custom (optional). 256 to 3840, step 16 |
| custom_height | Int | 1024 | Height when size is Custom (optional). 256 to 3840, step 16 |
| quality | Combo | auto | Image quality: auto, low, medium, high, xhigh, max (optional). xhigh/max on GPT Image 2.6 and 2.5 only (clamped to high on gpt-image-2) |
| moderation | Combo | auto | Content filter strictness: auto or low (optional). See Notes |
| n | Int | 1 | Number of images to generate (optional). Range: 1–10 |
| background | Combo | auto | auto, transparent, opaque (optional). Transparent works on GPT Image 2.6 and 2.5 only and needs png or webp output; gpt-image-2, or transparent with jpeg, is refused before the call |
| input_fidelity | Combo | auto | auto, high, low (optional). Ignored by every current model: gpt-image-2, 2.5 and 2.6 always edit at high fidelity and reject the field, so it is never sent. Kept so saved workflows load |
| seed | Int | -1 | Cache control only, not sent to the API. -1 randomizes (re-runs every queue); a fixed value reuses the cached result |
| output_format | Combo | png | Output file format: png, jpeg, webp (optional). `transparent` background needs png or webp |
| output_compression | Int | 100 | Compression 0–100 (optional). Sent only with jpeg or webp; png sends neither field |
| grid_images | String | `[]` | Hidden. The grid stores its ordered file list here as a JSON array of names in the `input` folder |
| complexity | Combo | auto | How much detail the edit holds: auto, low, medium, high (optional). GPT Image 2.6 only; `auto` sends nothing, which OpenAI documents as high. On other models the node leaves it out and logs a note, since they reject it |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | Image | Edited image tensor |

## Markup

Draw the marks (an arrow, a circle, a word) on a transparent layer the same size as image 1, save it as a PNG, and load it with Load Image. Connect its IMAGE to `markup` and its MASK to `markup_mask`. The node sends one RGBA PNG: color from `markup`, and alpha from `markup_mask` (Load Image sets the mask to 1 where the PNG is transparent). Without `markup_mask`, every pixel that is not pure black counts as a mark.

- The prompt says what to do at the marks, for example `put a yellow apple inside the red circle, then remove the circle`.
- `markup` must match image 1 in size, and `markup_mask` must match `markup`. A PNG with no alpha channel gives a 64x64 Load Image mask, which the node refuses with both sizes named.
- The node refuses `markup` together with `mask`, and `markup_mask` without `markup`.
- OpenAI names GPT Image 2.5 and 2.6 for markup. gpt-image-2 also followed a circle drawn off-center (measured 2026-11-05). On 2.5 and gpt-image-2 the API refuses an empty layer ("No actionable edit annotations were found").

## Image grid

With nothing connected to `image`, the node sends the files on its grid instead. While `image` is connected, the grid dims, shows `Image socket connected, grid ignored`, and takes no new files, but keeps the files it has. The grid works as on the Image Grid Loader node: pick or drop PNG, JPG, or WebP files, drag a cell to reorder it, click a cell to see the image full size, and hover a cell and click **×** to remove it. Click **Reference images** at the top of the grid to collapse it to its header, which still shows the count, and click it again to expand it. The number on each cell is the image's position in the request.

- Each file goes to the API as its own image, at its own size, in cell order. The node does not batch or letterbox them.
- The grid holds no more images than the selected model takes. OpenAI documents one limit for every GPT Image model, so the 2.6 and 2.5 tiers and gpt-image-2 each take up to 16 images.
- The node applies EXIF orientation, drops any alpha channel, and sends each file as PNG.
- A mask or a markup layer applies to the first image and must have that image's height and width.
- When you queue, ComfyUI checks that every grid file exists in the `input` folder, even with `image` connected. Clear the grid if it names a missing file.

Grid errors name what is at fault:

- `Connect an image or add images to the grid`: `image` is not connected and the grid is empty.
- `grid_images entry 2 not found in ComfyUI's input directory: 'cat.png'`: the file no longer exists under that name in `input`.
- `grid_images entry 1 is outside ComfyUI's input directory: '../cat.png'`: the entry leaves the `input` folder.
- `The grid holds 17 images but gpt-image-2 takes up to 16 images; remove 1`: the grid holds more images than the selected model takes.

## Notes

- **`moderation` is a request, not a guarantee**: `low` asks OpenAI for less restrictive filtering. Measured on 2026-09-17, both GPT Image 2.5 models honour it for artistic nudity while gpt-image-2 does not, and gpt-image-2.5-sunburst was inconsistent across identical requests. Graphic violence is refused at both levels on every model. OpenAI documents no per-model difference, so this can change without notice.
- **Refusals are legible**: a blocked request reports whether the prompt or the generated image was refused, plus the categories involved. A prompt-stage refusal is often fixable by rewording; an output-stage one usually is not.
- **System instructions do not apply**: the images endpoint accepts only a prompt, with no system or instructions field. Connecting an OpenAI System Instruction node upstream has no effect here; fold that guidance into the prompt. The OpenAI Image via Responses node is the one image path that does honour it.
- **Sizes were measured live on 2026-09-21**: 512x512 and 256x256 are rejected by every model this node offers, `auto` works everywhere, and 1536x864 works on gpt-image-2 and the 2.5 models. Sizes outside the gpt-image-2 envelope are rejected before the request is sent.
- gpt-image-1.5, gpt-image-1 and gpt-image-1-mini were removed on 2026-10-01. A saved workflow that names one fails validation until a current model is picked
- **Workflows saved before custom_width / custom_height existed load unchanged**: a typed size that is not a preset is restored as Custom with the dimensions filled in.
- **Workflows saved before complexity existed load with complexity auto**: complexity follows the grid's list in the saved values, so an older save restores the grid's own empty slot into it, and the node resets that to auto on load. The grid's files and every other value load unchanged.
- Without a mask, the model edits the entire image based on the prompt
- With a mask, only white areas are modified (inpainting mode)
- The mask is converted to an alpha channel internally — white regions become transparent for the API
