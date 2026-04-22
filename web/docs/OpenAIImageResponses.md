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
| `client` | OPENAI_API_CLIENT (optional) | — | Provided by an OpenAI API Config node. Optional if API key is in ComfyUI Settings / env / config.ini. |
| `mainline_model` | Combo | `gpt-5.4` | Text/reasoning model that drives the call. Options: gpt-5.4, gpt-5.4-mini/nano, gpt-5.2, gpt-5, gpt-5-mini/nano, gpt-4.1, gpt-4.1-mini, gpt-4o, gpt-4o-mini, o3, o4-mini. |
| `image_model` | Combo | `gpt-image-2` | GPT Image model used for pixel generation inside the tool. Options: gpt-image-2, gpt-image-1.5, gpt-image-1, gpt-image-1-mini. |
| `reasoning_effort` | Combo | `none` | Mainline-model reasoning depth: none / minimal / low / medium / high / xhigh. Only supported on reasoning-capable mainline models. |
| `size` | Combo | `1024x1024` | Image size. gpt-image-2 requires at least 655,360 pixels — small sizes like 512x512 are rejected at preflight. |
| `quality` | Combo | `auto` | Image quality tier (auto / low / medium / high). |
| `background` | Combo | `auto` | Background: auto / transparent / opaque. gpt-image-2 rejects transparent and auto-coerces to opaque with a warning. |
| `output_format` | Combo | `png` | Output image format: png, jpeg, webp. |
| `moderation` | Combo | `auto` | Content moderation: auto (default safety) or low (relaxed). |
| `enable_web_search` | Boolean | `false` | Add the web_search tool alongside image_generation. Mainline model decides whether to invoke it. Adds $10/1000 calls when used. |
| `api_key` | String (optional) | — | OpenAI API key (use if not configured in ComfyUI Settings). |
| `seed` | Int | -1 | Cache-bust seed. -1 randomizes every run. |

## Outputs

| Output | Type | Description |
|---|---|---|
| `image` | IMAGE | Generated image as a ComfyUI tensor. If the model emits multiple images in a single response, they're stacked into a batch. |
| `revised_prompt` | STRING | The prompt after mainline-model revision. Useful for understanding how your input was interpreted. |
| `reasoning_summary` | STRING | Human-readable summary of the mainline model's reasoning when `reasoning_effort != none`. Empty otherwise. |

## Notes

- **Two models, not one**: `mainline_model` picks prompt interpretation / reasoning / tool orchestration; `image_model` picks pixel-level generation. They play different roles — don't confuse them.
- **Cost**: you pay mainline-model input tokens for the prompt, mainline-model output tokens for reasoning (if enabled), and image_model output tokens for the image. Reasoning at high/xhigh can exceed the image cost itself.
- **Organization verification**: same requirement as gpt-image-2 via the direct endpoint.
- **No `n > 1`**: the Responses API emits one image per `image_generation_call`. For bulk generation use the direct OpenAI Image Generation node.
- **Batched output supported**: if the mainline model makes multiple tool calls in a single response, all images are stacked into the IMAGE batch tensor.

## Example workflows

- Generate an image with auto prompt revision: default settings, just set `prompt` and run.
- Reasoning-enhanced composition: set `reasoning_effort=medium`, prompt the model to reason about layout / style before generating.
- Research-assisted image: enable `enable_web_search`, prompt like "Find the current logo of [company] and render a mascot next to it." The model can search before generating.
