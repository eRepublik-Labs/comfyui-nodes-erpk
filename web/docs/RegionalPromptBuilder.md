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
| desc_1 … desc_6 | String | optional sockets | Override the matching region's description at execute time (numbered as on the canvas). Exposed via the inspector's plug button. |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| prompt | STRING | The assembled scene + layout prompt. Connect to an image node's prompt input. |
| bboxes | BOUNDING_BOX | Pixel-space boxes for the drawn regions, compatible with core bbox nodes. |
| width | INT | The frame width, passed through. |
| height | INT | The frame height, passed through. |
| image | IMAGE | The reference image, passed through unchanged. |

## Canvas editor

- **Draw** by dragging on empty space; **Ctrl/Cmd-drag** force-draws over existing boxes.
- **Click** selects; **Shift-click** toggles; **Shift-drag** marquees; dragging any selected region moves the whole selection; corner handles resize a single selection.
- **Alt-click** cycles overlapping regions; **double-click** jumps to the description field.
- **Right-click** opens the region list (top = front): click selects, drag rows to reorder depth, duplicate or delete per row.
- **Del** removes the selection; **Ctrl/Cmd+C/V/D** copy, paste, duplicate; **[ ]** change depth; **H** hides the boxes. The `?` button shows the full cheat sheet.
- The inspector row edits the selected region's description, kind (object or rendered text), and literal text. Text regions preview their string in-frame.
- Optional grid with a typed cell size in frame pixels, color and opacity controls, and snap-to-grid. Preferences save with the workflow.

## Depth

Regions layer back to front: number 1 is backmost, and the prompt tells the model that later elements appear in front where regions overlap. Reordering renumbers the regions.

## Dynamic descriptions

Select a region and press the inspector's plug button to expose its `desc_N` socket, then wire any STRING node into it. A wired region shows a plug chip and diagonal hatching, and its description field locks. Wiring binds by canvas number, so reordering depth remaps which socket feeds which region.

## Notes

- The prompt calls regions invisible "placement areas" and forbids drawing them; detection vocabulary makes some models paint the boxes into the image. If a generation still shows rectangles, re-queue with a different seed.
- An empty canvas with an empty prompt raises an error; describe the scene or add at least one region.
- The node is a pure prompt builder: it makes no API calls and caches like any config node.
