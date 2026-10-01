<!-- ABOUTME: Help documentation for the OpenAIImageResponses ComfyUI node. -->
<!-- ABOUTME: Generates images via OpenAI's Responses API with reasoning and optional web search. -->

# OpenAI Image Generation (Responses)

Generate images through OpenAI's Responses API with the `image_generation` hosted tool. Adds capabilities not available on the direct `/v1/images/generations` endpoint — reasoning effort, web search integration, and mainline-model prompt revision.

## When to use this node vs. OpenAI Image Generation

Use **OpenAI Image Generation** (the direct endpoint) when you want:
- `n > 1` bulk generation in a single call
- Lowest-latency, simplest path

Use **OpenAI Image Generation (Responses)** when you want:
- Reasoning applied to prompt interpretation (`reasoning_effort`)
- Web search integration (model can look up reference material)
- Auto prompt revision by a reasoning-capable mainline model

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `prompt` | String (multiline) | — | Image description. The mainline model may auto-revise before handing to the image model. |
| `client` | OPENAI_API_CLIENT (optional) | — | Provided by an OpenAI API Config node. Optional if API key is in ComfyUI Settings or config.ini. |
| `mainline_model` | Combo | `gpt-6.1-sol` | Text/reasoning model that drives the call. Options: gpt-6.1-sol, gpt-6-astra, gpt-6-sol, gpt-6-luna, gpt-5.6-sol, gpt-5.6-terra, gpt-5.6-luna. Each accepted the image_generation tool on 2026-10-01. |
| `image_model` | Combo | `gpt-image-2` | GPT Image model used for pixel generation inside the tool. Options: gpt-image-2, gpt-image-2.5-sunburst, gpt-image-2.5-flare. |
| `reasoning_effort` | Combo | `none` | Mainline-model reasoning depth: none / minimal / low / medium / high / xhigh. `none` sends no effort, so the model uses its own default. `minimal` is rejected alongside the image tool (measured 2026-10-01) and is sent as `low`. |
| `verbosity` | Combo | `default` | Mainline-model output verbosity: default / low / medium / high. Shapes how chatty the model is independent of token caps. |
| `size` | Combo | `1024x1024` | Image size: 1024x1024, 1024x1536, 1536x1024, 1792x1024, 1024x1792, 2048x2048, 2048x1152, 2560x1440, 3840x2160, 2160x3840. Every image model needs at least 655,360 pixels, so 512x512 and 256x256 were removed on 2026-10-01. 3840x2160 / 2160x3840 are experimental per OpenAI. |
| `quality` | Combo | `auto` | Image quality tier: auto / low / medium / high / xhigh / max. xhigh/max on GPT Image 2.5 only (clamped to high on gpt-image-2). |
| `background` | Combo | `auto` | Background: auto / transparent / opaque, sent as chosen. Transparent works on GPT Image 2.5 only; gpt-image-2 rejects it, and the node stops before the call; it needs png or webp output. |
| `output_format` | Combo | `png` | Output image format: png, jpeg, webp. |
| `moderation` | Combo | `auto` | Content moderation: auto (default safety) or low (relaxed). |
| `enable_web_search` | Boolean | `false` | Add the web_search tool alongside image_generation. Mainline model decides whether to invoke it. Adds $10/1000 calls when used. |
| `seed` | Int | -1 | Cache-bust seed. -1 randomizes every run. |

## Outputs

| Output | Type | Description |
|---|---|---|
| `image` | IMAGE | Generated image as a ComfyUI tensor. If the model emits multiple images in a single response, they're stacked into a batch. |
| `revised_prompt` | STRING | The prompt after mainline-model revision. Useful for understanding how your input was interpreted. |
| `reasoning_summary` | STRING | Raw chain-of-thought from the mainline model when `reasoning_effort != none`. Empty otherwise. **Heads up**: OpenAI's reasoning models think about both the task *and* the response format (output channels, tool calls, message structure). The summary often mixes "how I approached this image" with "should I produce a final message alongside the tool call?" — it's genuinely what the model returned, not a curated creative rationale. If you only want the image, ignore this output. If you want the creative thinking, you may need to parse or skim past the orchestration-level chatter. |

## Notes

- **System instructions apply here**: a connected OpenAI System Instruction node is forwarded as the Responses API instructions parameter and steers `mainline_model`. The direct Image Generation and Image Edit nodes cannot use it.
- **`moderation` is a request, not a guarantee**: how much `low` relaxes filtering varies by `image_model` and is not documented by OpenAI. Refusals report whether the prompt or the image was blocked.
- **Two models, not one**: `mainline_model` picks prompt interpretation / reasoning / tool orchestration; `image_model` picks pixel-level generation. They play different roles — don't confuse them.
- **Cost**: you pay mainline-model input tokens for the prompt, mainline-model output tokens for reasoning (if enabled), and image_model output tokens for the image. Reasoning at high/xhigh can exceed the image cost itself.
- **Organization verification**: same requirement as gpt-image-2 via the direct endpoint.
- **No `n > 1`**: the Responses API emits one image per `image_generation_call`. For bulk generation use the direct OpenAI Image Generation node.
- **Batched output supported**: if the mainline model makes multiple tool calls in a single response, all images are stacked into the IMAGE batch tensor.

## Example workflows

- Generate an image with auto prompt revision: default settings, just set `prompt` and run.
- Reasoning-enhanced composition: set `reasoning_effort=medium`, prompt the model to reason about layout / style before generating.
- Research-assisted image: enable `enable_web_search`, prompt like "Find the current logo of [company] and render a mascot next to it." The model can search before generating.
