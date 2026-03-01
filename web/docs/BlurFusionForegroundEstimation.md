<!-- ABOUTME: Help documentation for the Foreground Refinement (BlurFusion) ComfyUI node. -->
<!-- ABOUTME: Refines foreground edges using blur-based color estimation to reduce bleeding. -->

# Foreground Refinement (BlurFusion)

Refines foreground edges using blur-based color estimation. Reduces color bleeding from the background at semi-transparent edges by estimating true foreground colors. Use after any background removal node to improve edge quality.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | Image | — | Input image (original, before background removal) |
| mask | Mask | — | Foreground mask from a background removal node |
| blur_radius | Int | 90 | Primary blur radius for foreground estimation (optional). Range: 1–255 |
| blur_radius_secondary | Int | 6 | Secondary blur radius for edge refinement (optional). Range: 1–255 |
| fill_background | Boolean | False | Fill background with solid color instead of transparent (optional) |
| background_color | String | #000000 | Hex color for background fill (optional). e.g., #00FF00 for green |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | Image | Refined foreground image (RGBA or RGB with fill) |
| mask | Mask | Original mask passed through unchanged |

## Notes

- Connect the original image and a mask from any background removal node
- The primary blur_radius controls global color estimation — higher values smooth more
- The secondary blur_radius refines edges — keep it small (3–10) for best results
- Based on the fast-foreground-estimation method by Photoroom
