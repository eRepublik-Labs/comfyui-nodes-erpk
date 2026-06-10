# ComfyUI Custom Nodes - ERPK Collection

[![Publish to Comfy Registry](https://github.com/eRepublik-Labs/comfyui-nodes-erpk/actions/workflows/publish.yml/badge.svg)](https://github.com/eRepublik-Labs/comfyui-nodes-erpk/actions/workflows/publish.yml)
[![Registry](https://img.shields.io/badge/ComfyUI-Registry-blue)](https://registry.comfy.org/publishers/erpk/nodes/comfyui-nodes-erpk)

A monorepo for ERPK's custom ComfyUI nodes, extending ComfyUI's functionality through integrations with various AI services and APIs.

**Current Version:** 2026.6.3 (CalVer)

## Repository Structure

```
ComfyUI-Custom-Nodes/
├── wavespeed/                     # WaveSpeed AI integration
│   ├── README.md                  # Package documentation
│   ├── nodes.py                   # Core nodes
│   ├── seedream_v4*.py            # Seedream V4 nodes (4 variants)
│   ├── seedream_v4_5*.py          # Seedream V4.5 nodes (4 variants)
│   ├── qwen_image_*.py            # Qwen Image nodes
│   └── wavespeed_api/             # API integration layer
├── claude/                        # Claude API integration
│   ├── README.md                  # Package documentation
│   ├── nodes.py                   # Core nodes
│   ├── prompt_enhancer.py         # Prompt enhancement node
│   ├── vision_analysis.py         # Image analysis node
│   └── claude_api/                # API integration layer
├── gemini/                        # Google Gemini API integration
│   ├── README.md                  # Package documentation
│   ├── nodes.py                   # All Gemini nodes
│   ├── veo_nodes.py               # Veo video generation nodes
│   └── gemini_api/                # API integration layer
├── openai/                        # OpenAI API integration
│   ├── README.md                  # Package documentation
│   ├── nodes.py                   # Core nodes (Config, Text, Vision, Chat)
│   ├── image_nodes.py             # Image generation/editing nodes
│   └── openai_api/                # API integration layer
├── grok/                          # xAI Grok API integration
│   ├── README.md                  # Package documentation
│   ├── nodes.py                   # Config, Text, Chat, Image nodes
│   ├── video_nodes.py             # Text-to-Video, Ref-to-Video, Edit, Extend
│   └── grok_api/                  # API integration layer
├── utils/                         # String and general utilities
│   ├── __init__.py                # Module exports
│   └── concat_strings.py          # String concatenation node
├── settings.py                    # ComfyUI settings reader for API keys
├── shared_workflows.py            # Shared workflows CRUD for multi-user
├── shared_workflows/              # Legacy storage fallback (gitignored)
└── web/                           # Frontend extensions
    ├── erpk_settings.js           # API key settings in ComfyUI Settings UI
    ├── shared_workflows.js        # Browse/save/delete shared workflows UI
    ├── node_migration.js          # V1→V3 node type rewriting for old workflows
    ├── aspect_ratio.js            # Aspect ratio display in node titles
    └── concat_strings.js          # Dynamic UI for concat strings node
```

## Available Node Packages

### ERPK/WaveSpeedAI

Custom nodes for WaveSpeed AI's image generation and editing APIs.

**Category in ComfyUI:** `ERPK/WaveSpeedAI`
**Version:** 2026.2.15

#### ByteDance Seedream V4 Models

- **Seedream V4** - Text-to-image generation with configurable dimensions (320-4096px)
- **Seedream V4 Sequential** - Multi-image generation with cross-image consistency (1-15 images, $0.027/image)
- **Seedream V4 Edit** - AI-powered image editing with text prompts (up to 10 reference images)
- **Seedream V4 Edit Sequential** - Multi-image editing with coherent results (1-15 images, $0.027/image)

#### ByteDance Seedream V4.5 Models

- **Seedream V4.5** - Enhanced typography and text rendering for posters, logos, UI (1024-4096px)
- **Seedream V4.5 Sequential** - Multi-image generation with typography support (1-15 images, $0.027/image)
- **Seedream V4.5 Edit** - Image editing with enhanced text rendering (up to 10 reference images)
- **Seedream V4.5 Edit Sequential** - Multi-image editing with typography (1-15 images, $0.027/image)

#### Qwen Image Models

- **Qwen Image Text-to-Image** - Bilingual text-to-image generation (Chinese/English, max 1536×1536, $0.02/image)
- **Qwen Image Edit** - Single image editing with bilingual prompts (256-1536px, $0.02/image)
- **Qwen Image Edit Plus** - Advanced editing with up to 3 reference images ($0.02/image)
- **Qwen Image 2.0 Text-to-Image** - Next-gen Qwen with Standard and Pro quality tiers
- **Qwen Image 2.0 Edit** - Next-gen Qwen editing with up to 3 reference images, Standard and Pro tiers

#### Video Generation

Video nodes return a STRING URL that works directly with the **Preview Anything** node for preview/download. Longer polling (10s interval, 15-minute timeout) handles multi-minute generation runs.

- **Bytedance Seedance 2.0 Text-to-Video** / **Image-to-Video** - Native audio-visual generation across four model variants (Seedance 2.0, Turbo, Fast, Fast Turbo). T2V supports reference images/videos/audios; I2V supports optional end frame. Turbo variants are 720p/1080p only.
- **Alibaba WAN 2.7 Text-to-Video** / **Image-to-Video** / **Video Extend** - WAN 2.7 with extension support for continuing existing clips
- **WaveSpeed Veo 3.1 Text-to-Video** / **Image-to-Video** - Google Veo 3.1 via WaveSpeed billing (distinct from the Gemini-direct Veo nodes under `ERPK/Gemini/Veo`)
- **Kling 3.0 Image-to-Video** - Kling v3.0 i2v with Standard and Pro quality tiers
- **Kling O3 Text-to-Video** / **Image-to-Video** - Kling's flagship O3 with Standard and Pro tiers
- **Lightricks LTX 2 Pro Text-to-Video** / **Image-to-Video** - LTX 2 Pro with enum durations (6/8/10s) and optional audio
- **WaveSpeed LTX 2.3 Text-to-Video** / **Image-to-Video** - LTX 2.3 with 480p/720p/1080p resolution, 5-20s duration, and seed control

LTX 2 Pro and LTX 2.3 are separate nodes (not a unified dropdown) because their APIs take different parameters — LTX 2 Pro has `generate_audio`, LTX 2.3 has `resolution`/`aspect_ratio`/`seed`.

The Kling (2.5 Turbo, 2.6, Elements) and LTX 2 Pro nodes expose a **seed** widget for cache control. These WaveSpeed endpoints have no API seed, so the value is not sent to the API: leaving it on "randomize" forces a fresh, re-billed generation on every queue, while a fixed value lets ComfyUI serve the cached result and skip the call. LTX 2.3's seed, by contrast, is a true generation seed sent to the API.

**Installation & Documentation:** See [wavespeed/README.md](wavespeed/README.md)

⚠️ **Note:** For the official WaveSpeed ComfyUI nodes and documentation, see the [official WaveSpeed ComfyUI repository](https://github.com/wavespeedai/ComfyUI-WaveSpeed).

### ERPK/Claude

Claude API integration for text generation, prompt enhancement, vision analysis, and conversational AI.

**Category in ComfyUI:** `ERPK/Claude`
**Version:** 2026.2.15

#### Nodes

- **Claude API Client** - Initialize Claude API connection with model selection (Opus 4.7, Sonnet 4.6, Opus 4.6, Haiku 4.5) and configuration. Optional if API key is configured in ComfyUI Settings or config.ini -- Claude nodes can run standalone.
- **Claude Prompt Enhancer** - Transform simple prompts into detailed descriptions with 51 artistic styles (photorealistic, cinematic, fantasy, cyberpunk, anime, oil painting, watercolor, and more)
- **Claude Vision Analysis** - Analyze images with Claude's multimodal capabilities (up to 20 images simultaneously). Optional per-node `model` override lets you use Opus 4.7 (2576px image resolution) for vision even when your client is configured with a different model.
- **Claude Text Generation** - General-purpose text completion and generation
- **Claude Conversation** - Multi-turn dialogues with context preservation and automatic memory management
- **Claude Conversation Info** - Display conversation statistics and token usage
- **Claude Tool Definition** - Build Anthropic tool definitions for structured output (chainable)
- **Claude Structured Output** - Force Claude to respond with structured JSON matching a tool schema
- **Claude Token Counter** - Count tokens and estimate API costs before making requests
- **Claude Usage Stats** - Track cumulative token usage and costs across all Claude nodes

**Key Benefits:**
- 51 artistic styles for prompt enhancement (photorealistic, cinematic, fantasy, anime, oil painting, impressionist, cyberpunk, and more)
- Claude Opus 4.7 support with adaptive thinking (1M context, automatic sampling-param handling)
- Prompt caching (up to 90% cost savings)
- Streaming support for real-time responses
- Automatic context window management
- Multi-image analysis capabilities
- Cost optimization with token counting

**Installation & Documentation:** See [claude/README.md](claude/README.md)

### ERPK/Gemini

Google Gemini API integration for text generation, vision analysis, multi-turn conversations, image generation, image editing, and **Veo video generation**.

**Category in ComfyUI:** `ERPK/Gemini` and `ERPK/Gemini/Veo`
**Version:** 2026.2.15

#### Nodes

- **Gemini API Config** - Initialize Gemini API connection (API key configuration). Optional if API key is configured in ComfyUI Settings or config.ini -- Gemini nodes can run standalone.
- **Gemini Text Generation** - General-purpose text generation with model selection (Gemini 3.1 Pro, 3 Pro, 3 Flash, 2.5 Pro, 2.5 Flash, 2.5 Flash-Lite)
- **Gemini Chat** - Multi-turn conversations with automatic context preservation
- **Gemini Vision** - Analyze images with multimodal capabilities
- **Gemini Image Generation** - Generate images from text descriptions (3.1 Flash, 3 Pro, 2.5 Flash models; up to 4K resolution, 14 aspect ratios, Google Search grounding)
- **Gemini Image Edit** - Edit and modify images with natural language prompts (up to 14 reference images, same model and resolution options)
- **Gemini System Instruction** - Set persistent system-level instructions to guide model behavior
- **Gemini Safety Settings** - Configure content safety filters (strict/balanced/permissive presets or custom)

#### Veo Video Generation Nodes

- **Veo Text to Video** - Generate videos from text prompts using Google's Veo models (Veo 3 includes synchronized audio)
- **Veo Image to Video** - Generate videos from an input image and optional text prompt

**Key Benefits:**
- Support for Gemini 3.1 Pro, 3 Pro, 3 Flash, 3.1 Flash-Lite, and Gemini 2.5 models
- **Thinking level** control across all models (none/minimal/low/medium/high) with automatic parameter translation — Gemini 3.x uses `thinking_level` enum, Gemini 2.5 uses `thinking_budget` integer behind the same UI
- **Veo video generation** with text-to-video and image-to-video (Veo 3 includes audio)
- Each node selects its own model for maximum flexibility
- State-of-the-art reasoning with Gemini 3.1 Pro and 2.5 Pro
- Image generation with Gemini 3.1 Flash (recommended), 3 Pro, and 2.5 Flash models (512px to 4K resolution)
- Image editing with natural language instructions (up to 14 reference images)
- Simple, straightforward API integration
- Vision capabilities with batch image support
- Flexible safety controls
- Native multi-turn conversation support

**Installation & Documentation:** See [gemini/README.md](gemini/README.md)

### ERPK/OpenAI

OpenAI API integration for text generation, vision analysis, multi-turn conversations, image generation, and image editing.

**Category in ComfyUI:** `ERPK/OpenAI`
**Version:** 2026.2.15

#### Nodes

- **OpenAI API Config** - Initialize OpenAI API connection (API key configuration). Optional if API key is configured in ComfyUI Settings or config.ini -- OpenAI nodes can run standalone.
- **OpenAI Text Generation** - General-purpose text generation with model selection (GPT-5.5, GPT-5.5 Pro, GPT-5.4 family, GPT-5.2, GPT-4o, GPT-4.1, o3, o3-mini, o3-pro, o4-mini) and optional `reasoning_effort` and `verbosity` controls
- **OpenAI Chat** - Multi-turn conversations with automatic context preservation, plus reasoning_effort and verbosity control on gpt-5.x models
- **OpenAI Vision** - Analyze images with GPT-5.5 / GPT-5.4 / GPT-4o vision capabilities
- **OpenAI System Instruction** - Set persistent system-level instructions to guide model behavior
- **OpenAI Image Generation** - Generate images with GPT-Image-2 (default), GPT-Image-1.5, GPT-Image-1, GPT-Image-1-Mini (DALL-E 3 deprecated 2026-05-12)
- **OpenAI Image Generation (Responses)** - Generate images via the Responses API with a mainline reasoning model (gpt-5.5 default) driving the `image_generation` hosted tool. Adds optional web search grounding and prompt revision.
- **OpenAI Image Edit** - Edit and inpaint images with natural language prompts

**Key Benefits:**
- Support for latest GPT-5.5 (premium flagship, 1.05M context, $5/$30 per MTok), GPT-5.5 Pro (extended-compute, $30/$180 per MTok, no streaming), GPT-5.4 family (flagship, pro, mini, nano), GPT-5.2, GPT-4.1, GPT-4o, and o-series reasoning models
- `reasoning_effort` parameter (none/minimal/low/medium/high/xhigh) for reasoning-capable models; ignored silently by non-reasoning models
- `verbosity` parameter (default/low/medium/high) for gpt-5.x models — shapes how chatty the response is independently of `max_tokens`; silently dropped for older models
- Image generation with GPT-Image-2 (latest flagship: 4K output, multilingual text, rebuilt architecture), GPT-Image-1.5 (still available, supports transparent background), GPT-Image-1, and GPT-Image-1-Mini (cost tier)
- DALL-E 3 shuts down 2026-05-12 — migrate to GPT-Image models
- Image editing with optional mask support for inpainting
- Multi-turn conversation with session management
- Automatic retry with exponential backoff
- JSON response format support

**Installation & Documentation:** See [openai/README.md](openai/README.md)

### ERPK/Grok

xAI Grok integration — text, multi-turn chat, image generation/editing (up to 3 source images), and full video coverage (text-to-video, reference-to-video, edit, extend).

**Category in ComfyUI:** `ERPK/Grok` and `ERPK/Grok/Video`
**Version:** 2026.5.15
**SDK requirement:** `xai-sdk>=1.14.0`

#### Text & Chat Nodes

- **Grok API Client** - Initialize the xAI client (optional for downstream nodes)
- **Grok Text Generation** - One-shot text completion via `grok-4.3` / `grok-3` / `grok-3-mini` / `grok-2`
- **Grok Chat** - Multi-turn conversation threaded via `GROK_CHAT_SESSION`

#### Image Nodes

- **Grok Image Generation** - Text-to-image, 8 aspect ratios, 1k/2k resolution, n=1..4 batched output
- **Grok Image Edit** - Single or multi-image editing (up to 3 source images per xAI's cap)

#### Video Nodes

- **Grok Text to Video** - Text-to-video, 1-15s, 7 aspect ratios, 480p/720p
- **Grok Reference to Video** - Up to 3 reference images guide generation; `<IMAGE_N>` token addressing
- **Grok Video Edit** - Edit existing video URL with text prompt (output capped at 720p)
- **Grok Video Extend** - Append N more seconds of new content to an existing video URL

**Installation & Documentation:** See [grok/README.md](grok/README.md)

### Background Removal (Removed)

Background removal nodes have been removed from this package. For background removal in ComfyUI, use [ComfyUI-RMBG](https://github.com/1038lab/ComfyUI-RMBG) instead.

### ERPK/utils

String manipulation and general utility nodes.

**Category in ComfyUI:** `ERPK/utils`

#### Nodes

- **Concatenate Strings** - Combine multiple text inputs with configurable delimiters. Supports up to 10 connectable inputs - drag STRING outputs from other nodes or enter text directly.
- **Seed** - Generate a seed value with optional min/max range clamping. Connect the output to any node's seed input to share a single seed.
- **Preview Anything** - Preview any value: text, markdown, image/video/audio/gif URLs, IMAGE tensors, and AUDIO dicts. Includes a Download button that saves the rendered content to your computer.
- **Regional Prompt Builder** - Draw regions on a canvas and emit a layout-aware prompt for any image generation model: each region becomes a verbal placement plus box_2d coordinates (works with the Gemini, OpenAI, and Grok image nodes). Also outputs pixel-space `BOUNDING_BOX` regions compatible with core SAM3 Detect, Draw BBoxes, and Crop By BBoxes nodes.

**Regional Prompt Builder features:**
- Canvas editor on the node: drag to draw, move, and resize regions; shift-click or a shift-drag marquee selects multiple regions and dragging any selected region moves the whole selection; Ctrl/Cmd-drag force-draws over existing boxes; Alt-click cycles through overlapping regions; Delete removes the selection; Ctrl/Cmd+C/V/D copy, paste, and duplicate; H hides the boxes for a clear view of the frame. An inspector row under the canvas edits the selected region's description, kind (object or rendered text), and literal text live; double-click a region to jump to its description field
- Right-click the canvas for a region list (top = front): click a row to select, drag rows to reorder depth, duplicate or delete per row
- Regions keep identity colors; text regions preview their literal text in-frame
- Depth control: regions layer back to front (number 1 is backmost). Reorder with `[` / `]` or the inspector's depth buttons; the prompt tells the model that later elements appear in front where regions overlap
- Status strip shows region count, selection, frame dimensions, and aspect ratio
- A `?` button in the status strip toggles a shortcuts cheat sheet over the canvas (Escape or an outside click dismisses it)
- Clear button in the status strip empties all regions (two-step confirm, no blocking dialog)
- Optional grid with a typed cell size in frame pixels (8-1024, default 64 - latent-friendly), a color picker plus opacity control, and snap-to-grid; drawing, moving, and resizing quantize to pixel multiples, and the preferences save with the workflow
- Optional reference image input: the connected image displays under the regions (LoadImage shows immediately) and passes through unchanged on an `image` output, so the builder sits inline in image-edit chains
- Dynamic descriptions: optional `desc_1`-`desc_6` STRING sockets override the matching region's description at execute time (numbered as on the canvas), so any text node can drive a region. Sockets stay hidden until exposed with the inspector's plug button (or already wired); socket labels carry the region's text, and the inspector locks a wired region's description field
- The prompt instructs the model to treat placement areas as invisible guides so boxes are not rendered into the image

**Concatenate Strings features:**
- 10 connectable text inputs (Text 1 through Text 10)
- Optional labels for each input (Label 1 through Label 10)
- Configurable delimiter with escape sequence support (\n, \t)
- Label placement options (same line or new line)
- Add/Remove buttons to dynamically manage inputs
- Visual separators between configuration and input sections

**Preview Anything features:**
- Accepts any value via a wildcard input
- Auto-detects type (image/video/audio by URL extension, markdown by syntax, IMAGE tensor, AUDIO dict)
- Optional `display_type` dropdown to force a specific renderer
- Download button saves content as `.txt`, `.md`, or the original media format
- **Copy button** in the toolbar: copies text/markdown to clipboard, or copies the current image (single-image and gallery-single views) as a PNG blob
- **Character counter** appears in the toolbar for text and markdown output
- **Image dimensions badge** (W × H) overlays the bottom-right of single-image previews
- Text and markdown stay at a fixed scrollable size (no auto-growth to canvas-swallowing heights); images, video, and audio still auto-fit to their aspect ratio
- Last rendered content persists across workflow reloads
- Optional `strip_metadata` toggle re-encodes image URL inputs to remove EXIF / ICC / XMP (GPS, camera info, timestamps) before download. Images only; IMAGE tensor inputs are already metadata-free.

### Shared Workflows (Multi-User)

In multi-user ComfyUI (`--multi-user`), each user's workflows are sandboxed. Shared Workflows provides a common directory where any user can save, browse, load, and delete workflow templates. Also works in single-user mode.

**Access:** Right-click the canvas > **ERPK** submenu, or open **ERPK Settings** to see the inline shared workflows list below your API keys.

- **Browse Shared Workflows...** - View all shared workflows with name, size, date, and authorship (created by / last edited by). Load any workflow into your canvas or delete it.
- **Share Current Workflow...** - Save the current canvas workflow to the shared directory. The name field is pre-populated from the current workflow tab.
- **Save to "[name]"** - Appears after loading or sharing a workflow. Saves directly to the linked shared workflow without opening a dialog.
- **Settings panel** - The ERPK Settings panel shows an inline shared workflows list with Load, Delete, and Share Current buttons.

**Linked save-back:** When you load a shared workflow or share one, the workflow name is linked. Subsequent edits can be pushed back to the shared copy via the "Save to" menu item. Other users see the updated version when they browse.

**Authorship tracking:** Each shared workflow records who created it and who last modified it. On overwrite, the original creator is preserved while the modifier is updated.

**Toast notifications:** Success/error feedback appears as a brief toast in the top-right corner for all save, load, and delete operations.

**Storage:** Workflows are saved as JSON files in `shared_workflows/` under the ComfyUI base directory (e.g., `~/Documents/ComfyUI/shared_workflows/`), alongside `input/`, `output/`, and `models/`. This location persists across plugin upgrades and ComfyUI restarts. Falls back to the extension directory when running outside ComfyUI. Each file uses an envelope format (`{meta, workflow}`) that stores authorship metadata alongside the workflow graph. No API keys or user-specific data are stored.

**API Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/erpk/shared_workflows` | GET | List all shared workflows (metadata including authorship) |
| `/erpk/shared_workflows/{name}` | GET | Get a single workflow by name |
| `/erpk/shared_workflows` | POST | Save a workflow (`{name, workflow}`); records user as author |
| `/erpk/shared_workflows/{name}` | DELETE | Delete a workflow by name |

### SaveImage Metadata Toggle

Adds a **strip_metadata** toggle to ComfyUI's built-in SaveImage node (and PreviewImage, which inherits it). When enabled, both the workflow JSON and prompt data are stripped from saved PNG files, producing clean images with no embedded ComfyUI metadata.

- **Per-node control** - Each SaveImage node gets its own boolean toggle; no global setting needed
- **Off by default** - Metadata is preserved unless you explicitly enable stripping
- **Prompt metadata also stripped** - Both `extra_pnginfo` (workflow graph) and `prompt` (API-format node data) are removed when enabled

### Auto-Clear Job History

Automatically removes completed jobs from the history panel after each run. Prevents the UI from slowing down during long sessions with many queued generations.

- **Off by default** - Enable via **Settings > ERPK > General > Auto-Clear Job History**
- **Delayed cleanup** - Waits 5 seconds after job completion so the frontend can fetch results before the history entry is removed
- **No restart needed** - Toggling the setting takes effect on the next completed job

## Installation

### Method 1: ComfyUI Manager (Recommended)

1. Open ComfyUI Manager
2. Click **Install Custom Nodes**
3. Search for `erpk`
4. Find **ERPK Custom Nodes** and click **Install**
5. Restart ComfyUI

### Method 2: ComfyUI Registry

Install directly from the [ComfyUI Registry](https://registry.comfy.org/publishers/erpk/nodes/comfyui-nodes-erpk) web interface.

### Method 3: Manual Installation

1. Navigate to your ComfyUI custom_nodes directory:
   ```bash
   cd /path/to/ComfyUI/custom_nodes/
   ```

2. Clone this repository as `erpk`:
   ```bash
   git clone https://github.com/eRepublik-Labs/comfyui-nodes-erpk.git erpk
   ```

3. Install dependencies:
   ```bash
   cd erpk
   pip install -r requirements.txt
   ```

4. Restart ComfyUI

### Post-Installation

1. Configure API keys for the services you want to use.
   The easiest way is via right-click on the canvas > **ERPK Settings**, or **Settings > ERPK > API Keys** in ComfyUI -- keys are stored per-user and never saved in workflows. In the ERPK Settings panel, API-key fields show a masked preview (e.g. `sk-a…kgAA`) and a small **Edit** affordance; click a key to reveal the input, blur to re-mask.

   API keys are resolved in priority order:
   1. **ComfyUI Settings** (recommended) -- right-click canvas > ERPK Settings
   2. **Widget input** -- api_key field on client/config nodes
   3. **Config file** -- `provider/config.ini`

   **Multi-user support:** In multi-user ComfyUI installations, each user's API keys are stored separately in their own `comfy.settings.json`. The correct user's keys are resolved automatically during workflow execution. A "Current user: [name]" banner appears in the ERPK Settings panel when multi-user mode is active.

   - **WaveSpeed:** See [wavespeed/README.md](wavespeed/README.md#installation)
   - **Claude:** See [claude/README.md](claude/README.md#installation)
   - **Gemini:** See [gemini/README.md](gemini/README.md#installation)
   - **OpenAI:** See [openai/README.md](openai/README.md#installation)
   - **Grok:** See [grok/README.md](grok/README.md#installation)

2. Find nodes under their respective categories: `ERPK/WaveSpeedAI`, `ERPK/Claude`, `ERPK/Gemini`, `ERPK/OpenAI`, `ERPK/Grok`, and `ERPK/utils`

## Backward Compatibility

This package uses the ComfyUI V3 node API. Saved workflows that reference older node IDs (e.g. `"WaveSpeed Custom SeedreamV4"`) are automatically migrated to the current node IDs at load time via ComfyUI's NodeReplace system. No manual workflow editing is required.

## ComfyUI API Integration

ComfyUI provides a REST API that allows programmatic workflow creation and execution. This is useful for automation, testing, and integration with external tools.

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/system_stats` | GET | System information (OS, RAM, GPU, versions) |
| `/object_info` | GET | List all available nodes and their input/output types |
| `/prompt` | POST | Queue a workflow for execution |
| `/queue` | GET | View pending and running jobs |
| `/history` | GET | View execution history and results |
| `/history/{prompt_id}` | GET | Get results for a specific execution |

### Submitting a Workflow via API

```bash
curl -X POST http://localhost:8188/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {
      "1": {
        "class_type": "GeminiAPIConfig",
        "inputs": {
          "api_key": ""
        }
      },
      "2": {
        "class_type": "GeminiTextGeneration",
        "inputs": {
          "client": ["1", 0],
          "prompt": "Write a haiku about ComfyUI",
          "model": "gemini-2.5-flash",
          "temperature": 0.7,
          "max_tokens": 256
        }
      },
      "3": {
        "class_type": "PreviewAny",
        "inputs": {
          "source": ["2", 0]
        }
      }
    }
  }'
```

**Note:** The port may vary (8000 for desktop app, 8188 for standard installation).

### Workflow JSON Format

Workflows can be saved as JSON files in your ComfyUI workflows directory. The format includes:

- `nodes`: Array of node definitions with `id`, `type`, `pos`, `inputs`, `outputs`, and `widgets_values`
- `links`: Array of connections in format `[link_id, source_node, source_slot, target_node, target_slot, type]`
- `last_node_id` / `last_link_id`: Tracking for ID generation

### Checking Available Nodes

```bash
# List all ERPK nodes
curl -s http://localhost:8188/object_info | jq 'keys' | grep -i -E "(gemini|claude|openai)"
```

## License

MIT License
