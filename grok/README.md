# Grok (xAI) API Integration for ComfyUI

Complete xAI Grok integration providing text generation, multi-turn chat, image generation and editing, and **video generation (text-to-video, reference-to-video, edit, extend)** for ComfyUI workflows.

**Version:** 2026.5.15
**Category in ComfyUI:** `ERPK/Grok` and `ERPK/Grok/Video`
**SDK requirement:** `xai-sdk>=1.14.0` (declared in `pyproject.toml`)

## Features

- **Text Generation** — One-shot prompt → text via `grok-4.3` and earlier models
- **Multi-turn Chat** — Persistent conversation threading via the `GROK_CHAT_SESSION` custom type
- **Image Generation** — Text-to-image via `grok-imagine-image-quality` (1k/2k, 8 aspect ratios)
- **Image Editing** — Single or multi-image editing (up to 3 source images; xAI's documented cap)
- **Text-to-Video** — `grok-imagine-video`, 1–15 s clips, 7 aspect ratios, 480p or 720p
- **Reference-to-Video** — Guide generation with up to 3 reference images; address them inline via `<IMAGE_N>` tokens
- **Video Edit** — Edit an existing video URL with a text prompt (output capped at 720p per xAI)
- **Video Extension** — Append new content to an existing video by N more seconds
- **Concurrent execution** — All nodes are async; multiple Grok jobs in the same workflow execute concurrently (per the v2026.5.13 async parallelism work)

## Installation

### Prerequisites

- ComfyUI installed and running
- Python 3.10 or higher
- xAI API key ([get one here](https://x.ai/api))

### Steps

1. **Install the package** (if not already installed via the parent `comfyui-nodes-erpk`):
   ```bash
   pip install xai-sdk>=1.14.0
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
| **Grok Image Generation** | `IMAGE` (batched, n images) | Text-to-image, 1k/2k, 8 aspect ratios |
| **Grok Image Edit** | `IMAGE` | Edit 1–3 source images with a text prompt |

### Video (4)

| Node | Output | Purpose |
|---|---|---|
| **Grok Text to Video** | `STRING` (video URL) | Text-to-video, 1–15 s, 7 aspect ratios, 480p/720p |
| **Grok Reference to Video** | `STRING` (video URL) | Up to 3 reference images guide the generation; use `<IMAGE_1>`/`<IMAGE_2>`/`<IMAGE_3>` tokens in the prompt |
| **Grok Video Edit** | `STRING` (video URL) | Edit existing video by HTTPS URL — output inherits source duration/aspect/resolution (capped at 720p) |
| **Grok Video Extend** | `STRING` (video URL) | Append N seconds of new content to an existing video URL |

## Models

| Model ID | Used by | Notes |
|---|---|---|
| `grok-4.3` | Text Generation, Chat (default) | Latest Grok text model |
| `grok-3`, `grok-3-mini`, `grok-2` | Text Generation, Chat | Available via the model Combo input |
| `grok-imagine-image-quality` | Image Generation, Image Edit | Only image model currently available |
| `grok-imagine-video` | All video nodes | Only video model |

## Notes

- **Polling is abstracted** — the xAI SDK polls internally for video jobs. ComfyUI's executor sees one long async call per node, releasing the event loop while waiting.
- **xAI uses `application/json` bodies** for image edits (not multipart). Tensors are converted to base64 PNG data URIs automatically by `grok_api/utils.py`.
- **Reference images are converted automatically** in Grok Reference to Video. Pass a batched IMAGE tensor of up to 3 frames.
- **Output video URLs are time-limited** — chain into a Preview Video node to save locally if needed.
- **Concurrency**: multiple Grok nodes in the same workflow run concurrently. Combined with `ERPK.PARALLEL_WORKERS > 1`, you can also run separate workflows in parallel.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `xai-sdk is required` | `pip install xai-sdk>=1.14.0` |
| `No xAI API key found` | Configure via Settings, the node's api_key input, or config.ini (see Installation step 2) |
| Video node returns empty URL | Check xAI status; the SDK already retried internally |
| Image edit raises "Could not convert input image to a data URI" | Check that the input IMAGE tensor is a valid (B, H, W, C) float tensor |

## Version

**Current Version:** 2026.5.15

**Last Updated:** May 2026
