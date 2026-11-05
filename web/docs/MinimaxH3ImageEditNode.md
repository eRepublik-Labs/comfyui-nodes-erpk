<!-- ABOUTME: Help documentation for the MiniMax H3 Image Edit ComfyUI node. -->
<!-- ABOUTME: Re-renders a subject from up to nine reference images per a text instruction. -->

# MiniMax H3 Image Edit

Re-renders the subject of 1 to 9 reference images into a new scene, outfit, pose or art style while preserving identity.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String (multiline) | (empty) | Edit instruction. Cite references as `<Picture 1>` through `<Picture 9>` |
| images | IMAGE | (none) | Reference images as a ComfyUI IMAGE batch, up to 9. Takes precedence over the grid and image_urls (optional) |
| image_urls | String | (empty) | Reference image URLs, up to 9, separated by commas or newlines, or a list. Fallback when images is not connected and the grid is empty (optional) |
| client | WAVESPEED_AI_API_CLIENT | (none) | WaveSpeed API client (optional if API key is in Settings) |
| aspect_ratio | Combo | auto | Output aspect ratio. auto follows the first reference image (optional) |
| resolution | Combo | 1k | 1k or 2k (optional) |
| output_format | Combo | jpeg | jpeg, png or webp (optional) |
| seed | Int | -1 | Generation seed, sent to the API (optional) |
| loras | MINIMAX_H3_LORAS | (none) | LoRA stack from the MiniMax H3 LoRA Stack node. When connected the call goes to the -lora twin (optional) |
| grid_images | String | `[]` | Hidden. The grid stores its ordered file list here as a JSON array of names in the `input` folder |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | The edited image as a ComfyUI IMAGE tensor |

## Cite references by tag

The instruction should name each reference by its bracket tag, for example:

```
Put the person from <Picture 1> in the jacket from <Picture 2>, standing on a rainy street at night.
```

## Cost

About $0.03 per image at 1k and $0.09 at 2k, plus about $0.005 for each reference beyond the first. With a LoRA stack connected the -lora twin adds a flat $0.015 per image.

## Image grid

With nothing connected to `images`, the node sends the files on its grid. Pick or drop PNG, JPG, or WebP files, drag a cell to reorder it, click a cell to see the image full size, and hover a cell and click **×** to remove it. Click **Reference images** at the top of the grid to collapse it to its header, which still shows the count, and click it again to expand it. While `images` is connected, the grid dims and the node ignores it.

- Each file goes to the API as its own image, at its own size, in cell order.
- The node applies EXIF orientation, drops any alpha channel, and sends each file as JPEG.
- The grid holds up to 9 files, the model's limit.
- The grid wins over `image_urls`, so the node reads the URL text only when the grid is empty.
- When you queue, ComfyUI checks that every grid file exists in the `input` folder, even with `images` connected.
- `Connect an image or add images to the grid, or enter at least one image URL` means `images`, the grid and `image_urls` are all empty.

## Notes

- At least one reference is required, as an IMAGE batch, a grid file or a URL
- More than 9 references raises an error that names the count, instead of dropping the extra ones
- The node sends IMAGE batches and grid files as base64 data URIs, and URLs as they are
