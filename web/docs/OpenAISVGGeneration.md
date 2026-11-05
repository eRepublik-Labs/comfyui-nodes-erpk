<!-- ABOUTME: Help documentation for the OpenAI SVG Generation ComfyUI node. -->
<!-- ABOUTME: Generates SVG markup with GPT Image 2.6 and a text model that writes it. -->

# OpenAI SVG Generation

Generates a vector image as SVG markup with GPT Image 2.6. The image model passes the drawing to a text model (`svg_model`), which writes the markup.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | (empty) | Description of the vector image to generate |
| client | OPENAI_API_CLIENT | — | OpenAI API client (optional when Settings holds the API key) |
| model | Combo | gpt-image-2.6-flare | Image model: gpt-image-2.6-sunburst, gpt-image-2.6-flare (optional). Only GPT Image 2.6 returns SVG |
| svg_model | Combo | gpt-6.1-sol | Text model that writes the SVG markup (optional). Offers the same models as the Responses image node |
| size | Combo | 1024x1024 | Size preset or Custom (optional). Same presets and Custom envelope as OpenAI Image Generation |
| custom_width | Int | 1024 | Width when size is Custom (optional). 256 to 3840, step 16 |
| custom_height | Int | 1024 | Height when size is Custom (optional). 256 to 3840, step 16 |
| quality | Combo | auto | Image quality: auto, low, medium, high, xhigh, max (optional) |
| complexity | Combo | auto | Amount of detail: auto, low, medium, high (optional). `auto` sends nothing, which OpenAI documents as high |
| background | Combo | auto | Background type: auto, transparent, opaque (optional) |
| seed | Int | -1 | Cache control only, not sent to the API. -1 randomizes (re-runs every queue); a fixed value reuses the cached result |

## Output

| Output | Type | Description |
|--------|------|-------------|
| svg | String | The SVG markup, starting with `<svg` |

## Notes

- Each run asks for one SVG. The API takes only `n=1` for SVG output, and it has no streaming, partial images, or compression for it.
- Nothing in this node turns the SVG into pixels. Save the string as a `.svg` file, or pass it to a node that renders SVG.
- On 2026-11-05 gpt-6.1-sol returned SVG as `svg_model` on both 2.6 tiers. The node also offers the other text models of the Responses image node, which nobody has yet run as `svg_model`.
- gpt-image-2 and the GPT Image 2.5 models answer 400 "SVG output is not supported for this model.", so the node offers only the 2.6 models.
