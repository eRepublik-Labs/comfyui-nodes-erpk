# Grok (xAI) API Integration for ComfyUI

Complete xAI Grok integration providing text generation, multi-turn chat, image generation and editing, and **video generation (text-to-video, reference-to-video, edit, extend)** for ComfyUI workflows.

**Version:** 2026.9.11
**Category in ComfyUI:** `ERPK/Grok` and `ERPK/Grok/Video`
**SDK requirement:** `xai-sdk>=1.20.0` (declared in `pyproject.toml`; 1.18 added `xhigh` reasoning effort, 1.19 image `quality`)

## Features

- **Text Generation** — One-shot prompt → text via `grok-4.7` and other Grok models, with a `reasoning_effort` control for grok-4.7
- **Multi-turn Chat** — Persistent conversation threading via the `GROK_CHAT_SESSION` custom type
- **Image Generation** — Text-to-image via `grok-imagine-image-2.0` (1k/2k, 13 aspect ratios plus auto, low/medium quality, 1–10 images)
- **Image Editing** — Single or multi-image editing (up to 5 source images; xAI's documented cap for grok-imagine-image-2.0)
- **Text-to-Video** — `grok-imagine-video` / `grok-imagine-video-1.5`, 1–15 s clips, 7 aspect ratios, 480p or 720p
- **Reference-to-Video** — Guide generation with up to 3 reference images; address them inline via `<IMAGE_N>` tokens
- **Video Edit** — Edit an existing video (URL or data URI) with a text prompt (output capped at 8.7 s and 720p per xAI)
- **Video Extension** — Append 2–10 seconds of new content to an existing video
- **Concurrent execution** — All nodes are async; multiple Grok jobs in the same workflow execute concurrently (per the v2026.5.13 async parallelism work)

## Installation

### Prerequisites

- ComfyUI installed and running
- Python 3.10 or higher
- xAI API key ([get one here](https://x.ai/api))

### Steps

1. **Install the package** (if not already installed via the parent `comfyui-nodes-erpk`):
   ```bash
   pip install "xai-sdk>=1.20.0"
   ```
   The dep is declared in `pyproject.toml`, so `pip install -e .` or `uv sync` pulls it automatically.

2. **Configure API key** (priority order, first non-empty wins):

   **Method 1: ComfyUI Settings** (Recommended)
   Settings > ERPK > API Keys > xAI (Grok) API Key. Keys here aren't saved into workflows so they don't leak when sharing.

   **Method 2: config.ini**
   ```ini
   [API]
   XAI_API_KEY = your-api-key-here
   ```
   Lives at `grok/config.ini`.

3. **Restart ComfyUI.** Look for `[ERPK] Loaded N V3 nodes` with N incremented by 9 (the Grok nodes).

## Nodes

### Configuration (1)

| Node | Output | Purpose |
|---|---|---|
| **Grok API Client** | `GROK_API_CLIENT` | Initializes the client. Optional — every other Grok node accepts a missing client and falls through the resolution chain on its own. |

### Text (2)

| Node | Output | Purpose |
|---|---|---|
| **Grok Text Generation** | `STRING` | One-shot prompt → text. Stateless. |
| **Grok Chat** | `STRING` + `GROK_CHAT_SESSION` | Stateful multi-turn dialog. Thread the `chat_session` output into the next Chat node's input to continue. |

### Image (2)

| Node | Output | Purpose |
|---|---|---|
| **Grok Image Generation** | `IMAGE` (batched, n images) | Text-to-image, 1k/2k, 13 aspect ratios plus auto, low/medium quality, n=1–10 |
| **Grok Image Edit** | `IMAGE` | Edit 1–5 source images with a text prompt |

### Video (4)

| Node | Output | Purpose |
|---|---|---|
| **Grok Text to Video** | `STRING` (video URL) | Text-to-video, 1–15 s, 7 aspect ratios, 480p/720p |
| **Grok Reference to Video** | `STRING` (video URL) | Up to 3 reference images guide the generation; use `<IMAGE_0>`/`<IMAGE_1>`/`<IMAGE_2>` tokens in the prompt |
| **Grok Video Edit** | `STRING` (video URL) | Edit an existing video by public URL or data URI — output inherits source duration (capped at 8.7 s), aspect and resolution (capped at 720p). grok-imagine-video only |
| **Grok Video Extend** | `STRING` (video URL) | Append 2–10 seconds of new content to an existing video (public URL or data URI). grok-imagine-video only |

## Models

| Model ID | Used by | Notes |
|---|---|---|
| `grok-4.7` | Text Generation, Chat (default) | Current Grok flagship (500k context, image input). The only model that takes `reasoning_effort` (low to xhigh) |
| `grok-4.20-0309-non-reasoning` | Text Generation, Chat | 1M context; rejects `reasoning_effort`, so the node never sends it |
| `grok-4.20-multi-agent-0309` | Text Generation, Chat | 1M context; tighter rate limits (9 rps / 450 rpm) than its siblings; ignores `max_tokens` |
| `grok-build-0.1` | Text Generation, Chat | Coding model (replaces the retired grok-code-fast-1) |
| `grok-imagine-image-2.0` | Image Generation, Image Edit (default) | Per image: low $0.04 (1k) / $0.06 (2k); medium $0.06 (1k) / $0.08 (2k) |
| `grok-imagine-video` | All video nodes (default) | The only model with video input, so the only option on Video Edit and Video Extend |
| `grok-imagine-video-1.5` | Text to Video, Reference to Video | No video input |

Removed on 2026-10-01: `grok-4.6`, `grok-4.5`, `grok-4.3`, `grok-4.20-0309-reasoning`, `grok-imagine-image` and `grok-imagine-image-quality`. A saved workflow that selected one of them fails ComfyUI's validation until you pick a current model.

## Notes

- **Polling is abstracted** — the xAI SDK polls internally for video jobs. ComfyUI's executor sees one long async call per node, releasing the event loop while waiting.
- **xAI uses `application/json` bodies** for image edits (not multipart). Tensors are converted to base64 JPEG data URIs automatically by `grok_api/utils.py`, downscaled if needed so one request stays under the SDK's 20 MiB gRPC limit.
- **Reference images are converted automatically** in Grok Reference to Video. Pass a batched IMAGE tensor of up to 3 frames.
- **Output video URLs are time-limited** — chain into a Preview Video node to save locally if needed.
- **Concurrency**: multiple Grok nodes in the same workflow run concurrently. Combined with `ERPK.PARALLEL_WORKERS > 1`, you can also run separate workflows in parallel.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `xai-sdk is required` | `pip install "xai-sdk>=1.20.0"` |
| `No xAI API key found` | Configure via Settings, the node's api_key input, or config.ini (see Installation step 2) |
| Video node returns empty URL | Check xAI status; the SDK already retried internally |
| Image edit raises "Could not convert input image to a data URI" | Check that the input IMAGE tensor is a valid (B, H, W, C) float tensor |

## Version

**Current Version:** 2026.9.11

**Last Updated:** May 2026
