<!-- ABOUTME: Help documentation for the Gemini Image Edit ComfyUI node. -->
<!-- ABOUTME: Edits images using text prompts with Gemini's image generation models. -->

# Gemini Image Edit

Edits and modifies existing images using text prompts. Supports up to 14 reference images for multi-image editing tasks like style transfer and character consistency. Connect an image, or pick or drop image files onto the grid on the node.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | IMAGE | - | Reference image(s) to edit (optional). Use Batch Images node to combine multiple (up to 14). When connected, the node sends it and ignores the grid |
| prompt | String | "" | Describe the edit. Reference images by order, content, or role. |
| client | GEMINI_API_CLIENT | - | Gemini API client (optional, uses API key from config) |
| model | Combo | gemini-nano-banana-2.1 | Image model: gemini-nano-banana-2.1, gemini-3.1-flash-image (deprecated in favour of Nano Banana 2.1), gemini-3.1-flash-lite-image, gemini-3-pro-image (optional) |
| temperature | Float | 1.0 | Creativity level, 0.0-2.0. The image models report a maximum of 1.0; higher values are accepted without error but have no documented effect (optional) |
| aspect_ratio | Combo | default | Image aspect ratio: default, 1:1, 1:4, 1:8, 2:3, 3:2, 3:4, 4:1, 4:3, 4:5, 5:4, 8:1, 9:16, 16:9, 21:9. 3.1 Flash Lite and 3 Pro have no 1:4, 4:1, 1:8 or 8:1 and use the closest supported ratio (optional) |
| image_size | Combo | default | Resolution: default, 0.5K, 1K, 2K, 4K. 3.1 Flash takes 0.5K-4K, Nano Banana 2.1 and 3 Pro 1K-4K, 3.1 Flash Lite 1K only; an unsupported size uses the model's smallest size (optional) |
| response_modalities | Combo | IMAGE | IMAGE (image only) or TEXT+IMAGE (image + text description) (optional) |
| enable_google_search | Boolean | false | Enable Google Search grounding on Nano Banana 2.1, 3.1 Flash and 3 Pro; ignored on 3.1 Flash Lite, which does not support it (optional) |
| additional_images | IMAGE | - | Additional reference images, combined with primary input up to 14 total (optional) |
| image_refs | ERPK_IMAGE_REFS | - | Ordered reference images from a Regional Prompt Builder; sent right after the primary image so the prompt's image numbers line up (optional) |
| grid_images | String | `[]` | Hidden. The grid stores its ordered file list here as a JSON array of names in the `input` folder |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Edited image tensor |
| description | String | Text description (only populated when response_modalities is TEXT+IMAGE) |

## Image grid

With nothing connected to `image`, the node sends the files on its grid instead. While `image` is connected, the grid dims, shows `Image socket connected, grid ignored`, and takes no new files, but keeps the files it has. The grid works as on the Image Grid Loader node: pick or drop PNG, JPG, or WebP files, drag a cell to reorder it, and hover a cell and click **×** to remove it. Click **Reference images** at the top of the grid to collapse it to its header, which still shows the count, and click it again to expand it. The number on each cell is the image's position in the request.

- Each file goes to the model as its own image, at its own size, in cell order. The node does not batch or letterbox them.
- The grid holds up to 14 files on every model (Google documents 14 for Nano Banana 2.1, 3.1 Flash and 3 Pro). 3.1 Flash Lite has no documented limit and Google says it is not optimized for multiple reference inputs, so expect weaker results with many files there.
- The node applies EXIF orientation, drops any alpha channel, and sends each file as PNG.
- The grid files take the place of the `image` input. `image_refs` go right after the first grid file, then the remaining grid files, then `additional_images`.
- When you queue, ComfyUI checks that every grid file exists in the `input` folder, even with `image` connected. Clear the grid if it names a missing file.

Grid errors name what is at fault:

- `Connect an image or add images to the grid`: `image` is not connected and the grid is empty.
- `grid_images entry 2 not found in ComfyUI's input directory: 'cat.png'`: the file no longer exists under that name in `input`.
- `grid_images entry 1 is outside ComfyUI's input directory: '../cat.png'`: the entry leaves the `input` folder.
- `The grid holds 15 images but gemini-3-pro-image takes up to 14 images; remove 1`: the grid holds more images than the selected model takes.

## Notes

- Reference images in prompts by order ("the first image"), content ("the logo"), or role ("the style reference")
- Gemini 3 Pro supports up to 14 reference images (up to 6 objects, up to 5 humans for character consistency)
- Nano Banana 2.1 supports up to 14 reference images (up to 10 objects, up to 4 characters)
- Images are sent in order: the first primary image (the `image` socket's first frame, or grid cell 1), then image_refs, then the remaining primary images, then additional_images. The first primary image is "the first image" in positional prompts
- A Regional Prompt Builder numbers its refs from image 2, after one base image. That stays true with any number of grid files or batch frames, because the refs always follow the first primary image
- API key resolved from ComfyUI Settings or config.ini — connect a `client` from Gemini API Config only when you need shared safety/system-instruction state across nodes
