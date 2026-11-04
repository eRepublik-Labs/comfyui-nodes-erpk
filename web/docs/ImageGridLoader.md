<!-- ABOUTME: Help documentation for the Image Grid Loader utility node. -->
<!-- ABOUTME: Loads picked or dropped image files as one IMAGE batch in grid order. -->

# Image Grid Loader

Pick or drop image files onto the grid on the node, and get them back as one `IMAGE` batch in grid order. Connect the output to any edit node that takes an `IMAGE` batch, such as Gemini Image Edit, OpenAI Image Edit, Grok Image Edit, MiniMax H3 Image Edit, the Qwen multi-image edit nodes, and the Seedream edit nodes.

This node does not call any API. It reads files from ComfyUI's `input` folder. The edit node you connect it to sends the images.

OpenAI Image Edit has the same grid built in. There, each file goes to the API at its own size, so the node does not letterbox mixed sizes. While that node's `image` input is connected, its grid dims and takes no new files, because the node sends the connected image instead. On OpenAI Image Edit, the grid also holds no more images than the selected model takes, which is 16 for every model.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| grid_max_images | Int | 14 | The most images the grid accepts, from 1 to 14. This node has no model, so this value alone sets the limit. Seedream edit nodes take up to 10 images and Gemini Image Edit takes up to 14. |
| grid_images | String | `[]` | Hidden. The grid stores its ordered file list here as a JSON array of names in the `input` folder, for example `["cat.png", "pasted/dog.jpg"]`. |

## Output

| Output | Type | Description |
|--------|------|-------------|
| IMAGE | `IMAGE` | One batch with one image per grid cell, in cell order. |

## Grid order

The number on each cell is the image's position in the batch. Cell 1 is the first image, cell 2 the second, and so on. A prompt that names images by position, such as "Picture 3", refers to cell 3. The numbers update after every move or removal.

## Use the grid

- **Choose files…** in the empty grid, or the **+ Add** cell, opens a file picker that accepts more than one file at a time.
- You can drop files from your file manager onto the grid.
- The grid accepts PNG, JPG, and WEBP files. It skips other file types and says how many it skipped.
- When you drop more files than the grid has free slots, it adds files up to `grid_max_images` and ignores the rest. The drop overlay shows how many free slots remain. It turns red when the grid is full.
- Drag a cell to reorder it. A green bar shows where it lands.
- Hover a cell and click **×** to remove it.
- **Clear all** empties the grid. Click **Undo** in the notice under the grid to bring the images back.
- The title bar and the footer show the count, for example `7 of 14`.

Keyboard: press Tab to focus a cell. The arrow keys move the focused image one place left or right, or one row up or down. Delete or Backspace removes it.

## Files

The grid uploads each picked or dropped file to ComfyUI's `input` folder through ComfyUI's standard image upload. If a file with the same name and different content is already there, ComfyUI saves the new file as `name (1).png`. If the same file is already there, ComfyUI reuses it. Removing a cell or clearing the grid does not delete files from `input`.

## Mixed sizes

All images in an `IMAGE` batch must share one height and width. When the files differ in size, the node places each image, unscaled and centered, on a canvas as tall as the tallest image and as wide as the widest. Mid-grey (0.5) fills the rest of the canvas. The node uses mid-grey rather than black so an edit model is less likely to read the bars as dark content. For the cleanest results, use images of the same size.

## Errors

Each error names what is at fault. ComfyUI reports the first three when you queue the prompt, before any node runs. It reports the `grid_max_images` error when this node runs.

- `Add at least one image`: the grid is empty.
- `grid_images entry 2 not found in ComfyUI's input directory: 'cat.png'`: the file no longer exists under that name in `input`. The cell shows **Missing**.
- `grid_images entry 1 is outside ComfyUI's input directory: '../cat.png'`: the entry is an absolute path, or it leaves the `input` folder through `..` or a symbolic link. The node only reads files inside `input`.
- `The grid holds 12 images but grid_max_images is 10; remove 2 or raise grid_max_images`: you lowered `grid_max_images` below the number of images in the grid. The footer turns red when this happens.

## Notes

- Images load as RGB. The node drops any alpha channel, and an animated file contributes its first frame.
- The node applies EXIF orientation, so a photo taken in portrait loads upright.
- The node has no seed. ComfyUI reuses its cached output until the file list or `grid_max_images` changes. If you replace a file in `input` under the same name outside ComfyUI, change the list or restart ComfyUI to load the new file.
