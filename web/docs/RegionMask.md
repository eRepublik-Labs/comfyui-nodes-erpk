<!-- ABOUTME: Help documentation for the Region Mask ComfyUI node. -->
<!-- ABOUTME: Picks one region's mask from the Regional Prompt Builder's masks batch by region number. -->

# Region Mask

Picks a single region's mask out of the Regional Prompt Builder's `masks` output, selected by canvas region number. Use it to target one object downstream (for example, to drive an inpaint or a compositing mask) without splitting the whole batch by hand.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| masks | MASK | (required) | Masks batch from the Regional Prompt Builder, one mask per region in region order. |
| region | INT | 1 | Canvas region number (1 = backmost, matching the numbers shown in the editor). Out-of-range numbers clamp to the batch. |

## Output

| Output | Type | Description |
|--------|------|-------------|
| mask | MASK | The selected region's mask, returned as a single-mask batch. |

## Notes

- The region number matches the numbers the Regional Prompt Builder shows on the canvas and in its layer list, where 1 is the backmost region.
- An out-of-range region number is clamped into the batch rather than erroring, so a wired number that drifts past the current region count still returns a valid mask.
- With an empty masks batch the node returns the batch unchanged (the clamp resolves to index 0).
