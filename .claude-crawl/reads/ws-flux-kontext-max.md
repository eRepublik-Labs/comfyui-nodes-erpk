[Home](https://wavespeed.ai/)/ [Explore](https://wavespeed.ai/models)/ [Flux Image Tools](https://wavespeed.ai/collections/flux)/wavespeed-ai/flux-kontext-max

# FLUX.1 Kontext Max

wavespeed-ai /

flux-kontext-max

Add to favouriteSchema

Copy content

## FLUX.1 Kontext \[max\] boosts prompt adherence and typography generation for consistent, high-quality image editing at speed. Ready-to-use REST inference API, best performance, no coldstarts, affordable pricing.

image-to-image

PlaygroundAPIHistory

InputForm

image\*

Drag & drop or click to upload

![preview](https://static.wavespeed.ai/examples/56d79800016c423386f4a1d74c6ad5ae/1753869194060945436_MJnIJZeh.jpeg)

prompt\*

Prompt Enhancer

seed

guidance\_scale

aspect\_ratio

Select Aspect Ratio

(empty)21:916:94:33:21:12:33:49:169:21

enable\_sync\_mode

If set to true, the function will wait for the result to be generated and uploaded before returning the response. It allows you to get the result directly in the response. This property is only available through the API.

Clear

Create for Free

Enable Safety Checker

Idle

PreviewJSON

![To toy style](https://static.wavespeed.ai/examples/56d79800016c423386f4a1d74c6ad5ae/1.jpg)

Enable Image Magnification

Your request will cost $0.08 per run.

For $1 you can run this model approximately 12 times.

One more thing:

Image UpscalerRemove BackgroundImage EraserGenerate Video

### ExamplesView all

![To toy style](https://static.wavespeed.ai/examples/56d79800016c423386f4a1d74c6ad5ae/1.jpg)

![To Punjabi style  ](https://static.wavespeed.ai/examples/ef2439462d6f48aca4790f1928b7e9df/1.jpg)

![To cartoon style](https://static.wavespeed.ai/examples/b3a3291daa7c4467822c2be5e029f02f/1.jpg)

![Transform into a Studio Ghibli style](https://static.wavespeed.ai/examples/4c509f29d60042af861302df22261669/1.jpg)

![Remove flying birds](https://static.wavespeed.ai/examples/63cc2408666b4e568c375d2c2d20083a/1.jpg)

![Add sunglasses for men](https://static.wavespeed.ai/examples/72d88d1c70cf4d06a8d5bf4d536ffadf/1.jpg)

![Change the man's posture, clasp his hands firmly](https://static.wavespeed.ai/examples/591ddb39e5d742c8a8ec91e8d20f0d28/1.jpg)

![Transform into oil painting style](https://static.wavespeed.ai/examples/6e0286cc2bb34e7da5089533b8e0968b/1.jpg)

![Become illustration style](https://static.wavespeed.ai/examples/cc3224aa3f614fed9696e5da889ecf52/1.jpg)

![Turn clothes into a white dress](https://static.wavespeed.ai/examples/951bca7f8bac4ad5917bb9f158cc92a3/1.jpg)

### Related Models

[![wavespeed-ai/flux-2-pro/edit](https://static.wavespeed.ai/static/2026-04-08/20260408110336_m9hlu97o.webp)\\
\\
flux-2-pro/edit\\
\\
image-to-image](https://wavespeed.ai/models/wavespeed-ai/flux-2-pro/edit) [![wavespeed-ai/flux-2-max/edit](https://static.wavespeed.ai/static/2026-04-08/20260408110906_3odup3t7.webp)\\
\\
flux-2-max/edit\\
\\
image-to-image](https://wavespeed.ai/models/wavespeed-ai/flux-2-max/edit) [![wavespeed-ai/flux-2-dev/edit-lora](https://static.wavespeed.ai/static/2026-04-08/20260408112148_tz211gyc.webp)\\
\\
flux-2-dev/edit-lora\\
\\
lora-support](https://wavespeed.ai/models/wavespeed-ai/flux-2-dev/edit-lora) [![wavespeed-ai/flux-2-dev/text-to-image-lora](https://static.wavespeed.ai/static/2026-04-08/20260408112142_640s9c02.webp)\\
\\
flux-2-dev/text-to-image-lora\\
\\
lora-support](https://wavespeed.ai/models/wavespeed-ai/flux-2-dev/text-to-image-lora) [![wavespeed-ai/flux-2-flex/text-to-image](https://static.wavespeed.ai/static/2026-04-08/20260408111315_4375yvb0.webp)\\
\\
flux-2-flex/text-to-image\\
\\
text-to-image](https://wavespeed.ai/models/wavespeed-ai/flux-2-flex/text-to-image) [![wavespeed-ai/flux-2-flex/edit](https://static.wavespeed.ai/static/2026-04-08/20260408111310_fmkh97ub.webp)\\
\\
flux-2-flex/edit\\
\\
image-to-image](https://wavespeed.ai/models/wavespeed-ai/flux-2-flex/edit)

### README

FLUX Kontext Max (Image-to-Image Editing) — wavespeed-ai/flux-kontext-max

Key capabilities

Typical use cases

Pricing

Inputs and outputs

Parameters

Prompting guide

Example prompts

Best practices

## FLUX Kontext Max (Image-to-Image Editing) — wavespeed-ai/flux-kontext-max

FLUX Kontext Max is a premium image-to-image editing model built for high-fidelity, instruction-following transformations. Provide a source image plus a natural-language edit prompt, and it performs precise local or global edits while maintaining strong visual coherence—ideal for demanding creative direction, high-end retouching, and style-driven transformations.

## Key capabilities

- High-fidelity instruction-based image editing from a single input image
- Strong prompt adherence for complex, multi-constraint edits
- Handles both local edits (specific elements) and global edits (overall look)
- Excellent for style transformations (e.g., toy style, clay, illustration) while preserving composition

## Typical use cases

- Premium retouching: lighting correction, cleanup, detail enhancement
- Background swaps with consistent lighting/shadows
- Product and branding edits requiring high accuracy
- Style transformations with minimal drift (toy, clay, cinematic, illustration)
- Creative iterations where output quality matters more than speed

## Pricing

$0.08 per image.

## Inputs and outputs

Input:

- image (required): Source image (upload or public URL)
- prompt (required): Edit instruction

Output:

- One or more edited images (controlled by num\_images, if available in your interface)

## Parameters

- prompt (required): Edit instruction describing what to change and what to preserve
- image (required): Source image
- seed: Fixed value for reproducibility; leave empty/random for variation
- guidance\_scale: Prompt adherence strength (higher = stricter; too high may over-edit)
- aspect\_ratio: Output aspect ratio (choose to control framing/cropping)

## Prompting guide

For best control, use a “preserve + edit + constraints” structure:

Template:
Keep \[what must stay\]. Change \[what to edit\]. Ensure \[constraints\]. Match \[lighting/shadows/perspective\].

## Example prompts

- Keep the person’s face, pose, and clothing unchanged. Convert the entire image to a high-quality toy style with realistic plastic texture, soft studio lighting, and clean highlights. Keep the background composition consistent.
- Keep the subject identity and expression unchanged. Replace the background with a clean pastel studio backdrop. Match lighting direction and shadow softness.
- Remove background clutter and keep the main subject sharp. Apply a gentle cinematic color grade without changing composition.

## Best practices

- Start with one change per run, then iterate for precision.
- If the edit is too strong, lower guidance\_scale and add a clearer preserve clause.
- Fix seed for stable comparisons across prompt variants.
- Choose aspect\_ratio intentionally to avoid unexpected cropping.

Create Team

Team Name

Create

We use cookies to improve your experience and analyze website traffic. [Learn more](https://wavespeed.ai/static/privacy)

RejectAccept

Chatwoot
