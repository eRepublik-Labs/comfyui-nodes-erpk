<!-- ABOUTME: Help documentation for the Regional Prompt Builder utility node. -->
<!-- ABOUTME: Canvas region editor that assembles a layout-aware prompt plus pixel bounding boxes. -->

# Regional Prompt Builder

Draw regions on a canvas and emit a layout-aware prompt for any image generation model. Each region becomes a verbal placement plus precise coordinates, so models place elements where you drew them. Works with the Gemini, OpenAI, and Grok image nodes; the `bboxes` output feeds core BOUNDING_BOX nodes (SAM3 Detect, Draw BBoxes, Crop By BBoxes).

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| width | Int | 1024 | Target frame width in pixels (64-8192, step 8). |
| height | Int | 1024 | Target frame height in pixels (64-8192, step 8). |
| prompt | String | — | Scene description: subject, setting, background, style. Regions are placed on top of this scene. |
| regions_data | String | [] | Managed by the canvas editor; JSON list of normalized regions. Do not edit by hand. |
| image | IMAGE | optional | Reference image shown under the regions and passed through unchanged, so the builder sits inline in an image-edit chain. |
| desc_1 … desc_10 | String | optional sockets | Override the matching region's description at execute time (numbered as on the canvas). Exposed via the inspector's plug button. |
| ref_1 … ref_10 | IMAGE | optional sockets | Attach a reference image to the matching region. Exposed via the inspector's ▣ button; forwarded on image_refs in region order. |
| regions | ERPK_REGIONS | optional | Detected regions (JSON) appended after the canvas regions at execute time. Wire from a detector node. |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| prompt | STRING | The assembled scene + layout prompt. Connect to an image node's prompt input. |
| bboxes | BOUNDING_BOX | Pixel-space boxes for the drawn regions, compatible with core bbox nodes. |
| width | INT | The frame width, passed through. |
| height | INT | The frame height, passed through. |
| image | IMAGE | The reference image, passed through unchanged. |
| image_refs | ERPK_IMAGE_REFS | Wired region reference images in region order; connect to Gemini Image Edit's image_refs input. |
| masks | MASK | A frame-sized mask batch, one per region in region order. Scanned regions use their stored segmentation; all other regions get filled rectangles. |

## Canvas editor

- **Draw** by dragging on empty space; **Ctrl/Cmd-drag** force-draws over existing boxes.
- **Click** selects; **Shift-click** toggles; **Shift-drag** marquees; dragging any selected region moves the whole selection; corner handles resize a single selection.
- **Alt-click** cycles overlapping regions; **double-click** jumps to the description field.
- **Right-click** opens the region list (top = front): click selects, drag rows to reorder depth, duplicate or delete per row.
- **Del** removes the selection; **Ctrl/Cmd+C/V/D** copy, paste, duplicate; **[ ]** change depth; **H** hides the boxes; **F** (or the ⤢ button) expands the editor to fill the window, Esc exits. The `?` button shows the full cheat sheet.
- The inspector row edits the selected region's description, kind (object or rendered text), and literal text. Text regions preview their string in-frame.
- Optional grid with a typed cell size in frame pixels, color and opacity controls, and snap-to-grid. Preferences save with the workflow.

## Depth

Regions layer back to front: number 1 is backmost, and the prompt tells the model that later elements appear in front where regions overlap. Reordering renumbers the regions.

## Dynamic descriptions

Select a region and press the inspector's plug button to expose its `desc_N` socket, then wire any STRING node into it. A wired region shows a plug chip and diagonal hatching, and its description field locks. Wiring binds by canvas number, so reordering depth remaps which socket feeds which region.

## Region reference images

Select a region and press the inspector's ▣ button to expose its `ref_N` IMAGE socket, then wire any image into it. The region's prompt line becomes "taken from image N (reproduce that exact item)", and the wired images flow out on `image_refs` in region order. Keep the region's description consistent with the attached image — when the words and the picture disagree, models tend to follow the words. Connect that output to Gemini Image Edit's `image_refs` input: the node sends the edited image first (image 1), then the refs, so the prompt's numbering always matches what the model sees. Regions with a wired ref show a ▣ chip and a corner thumbnail on the canvas.

## Wired regions

The `regions` input accepts detected regions (JSON) from a detector node. They are appended after the canvas regions at execute time, so the canvas is never modified and detected regions are not visible on the canvas preview. Because numbering runs back to front, detected regions take the highest numbers and render in front of canvas regions where boxes overlap. The `desc_N` and `ref_N` overrides bind canvas regions only — they never apply to wired regions.

## Object scan

With an image connected, a ✦ button floats in the canvas's upper-left. Pressing it sends the image to the ComfyUI server, which runs Gemini (key from Settings — it never reaches the browser) to find the prominent objects. Each found object becomes a real, editable canvas region: its description is the object's label, same-class objects share a color family, and the model orders the scene back to front so depth comes pre-assigned. Segmentation masks are computed locally by a box-prompted segmentation model (weights download once on the first scan), drawn as a toggleable overlay (the mask button next to the scan button) and emitted on the `masks` output. Scanned regions append after anything already drawn; objects the model misses can be drawn by hand as usual.

Hovering the canvas glows the mask of the object under the cursor, and clicking selects by mask: a click in the empty part of a scanned region's box passes through to whatever is actually under the pointer, so overlapping objects stay individually selectable. Hand-drawn regions keep plain rectangle behavior, and Alt-click still cycles the stack explicitly. The Region Mask node picks one region's mask out of the `masks` batch by canvas number for inpainting chains.

Scanned objects can be repositioned: drag or scale a scanned region and its masked cut-out follows, with a dashed ghost marking the origin. The prompt then tells the model to move the object there and reconstruct the vacated background — the canvas previews the intent, and the edit model performs the actual move at generation time. Moving a region back to its origin restores the plain placement line.

## Notes

- The prompt calls regions invisible "placement areas" and forbids drawing them; detection vocabulary makes some models paint the boxes into the image. If a generation still shows rectangles, re-queue with a different seed.
- An empty canvas with an empty prompt raises an error; describe the scene or add at least one region.
- The node is a pure prompt builder: it makes no API calls and caches like any config node.
