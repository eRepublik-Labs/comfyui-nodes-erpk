# ComfyUI Custom Nodes - ERPK Collection

[![Publish to Comfy Registry](https://github.com/eRepublik-Labs/comfyui-nodes-erpk/actions/workflows/publish.yml/badge.svg)](https://github.com/eRepublik-Labs/comfyui-nodes-erpk/actions/workflows/publish.yml)
[![Registry](https://img.shields.io/badge/ComfyUI-Registry-blue)](https://registry.comfy.org/publishers/erpk/nodes/comfyui-nodes-erpk)

A monorepo for ERPK's custom ComfyUI nodes, extending ComfyUI's functionality through integrations with various AI services and APIs.

**Current Version:** 2025.12.18 (CalVer)

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
├── bgremoval/                     # Background removal utilities
│   ├── utils.py                   # Shared tensor/PIL conversion utilities
│   ├── rembg_node.py              # rembg backend (14+ ONNX models)
│   ├── inspyrenet_node.py         # InSPyReNet backend (PyTorch)
│   └── birefnet_node.py           # BiRefNet backend (HuggingFace)
├── apple/                         # Apple ML models integration
│   ├── README.md                  # Package documentation
│   └── sharp_nodes.py             # SHARP view synthesis nodes
└── web/                           # Frontend extensions
    └── aspect_ratio.js            # Aspect ratio display in node titles
```

## Available Node Packages

### ERPK/WaveSpeedAI

Custom nodes for WaveSpeed AI's image generation and editing APIs.

**Category in ComfyUI:** `ERPK/WaveSpeedAI`
**Version:** 2025.12.18

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

**Installation & Documentation:** See [wavespeed/README.md](wavespeed/README.md)

⚠️ **Note:** For the official WaveSpeed ComfyUI nodes and documentation, see the [official WaveSpeed ComfyUI repository](https://github.com/wavespeedai/ComfyUI-WaveSpeed).

### ERPK/Claude

Claude API integration for text generation, prompt enhancement, vision analysis, and conversational AI.

**Category in ComfyUI:** `ERPK/Claude`
**Version:** 2025.12.18

#### Nodes

- **Claude API Client** - Initialize Claude API connection with model selection (Sonnet 4.5, Opus 4, Haiku 4.5) and configuration. Required for all other Claude nodes.
- **Claude Prompt Enhancer** - Transform simple prompts into detailed descriptions with 51 artistic styles (photorealistic, cinematic, fantasy, cyberpunk, anime, oil painting, watercolor, and more)
- **Claude Vision Analysis** - Analyze images with Claude's multimodal capabilities (up to 20 images simultaneously)
- **Claude Text Generation** - General-purpose text completion and generation
- **Claude Conversation** - Multi-turn dialogues with context preservation and automatic memory management
- **Claude Token Counter** - Count tokens and estimate API costs before making requests
- **Claude Usage Stats** - Track cumulative token usage and costs across all Claude nodes

**Key Benefits:**
- 51 artistic styles for prompt enhancement (photorealistic, cinematic, fantasy, anime, oil painting, impressionist, cyberpunk, and more)
- Prompt caching (up to 90% cost savings)
- Streaming support for real-time responses
- Automatic context window management
- Multi-image analysis capabilities
- Cost optimization with token counting

**Installation & Documentation:** See [claude/README.md](claude/README.md)

### ERPK/Gemini

Google Gemini API integration for text generation, vision analysis, multi-turn conversations, image generation, image editing, and **Veo video generation**.

**Category in ComfyUI:** `ERPK/Gemini` and `ERPK/Gemini/Veo`
**Version:** 2025.12.18

#### Nodes

- **Gemini API Config** - Initialize Gemini API connection (API key configuration)
- **Gemini Text Generation** - General-purpose text generation with model selection (Gemini 3 Pro, 2.5 Pro, 2.5 Flash, 2.5 Flash-Lite)
- **Gemini Chat** - Multi-turn conversations with automatic context preservation
- **Gemini Vision** - Analyze images with multimodal capabilities
- **Gemini Image Generation** - Generate images from text descriptions (standalone node with dedicated image gen models)
- **Gemini Image Edit** - Edit and modify images with natural language prompts (supports 1-3 images)
- **Gemini System Instruction** - Set persistent system-level instructions to guide model behavior
- **Gemini Safety Settings** - Configure content safety filters (strict/balanced/permissive presets or custom)

#### Veo Video Generation Nodes

- **Veo Text to Video** - Generate videos from text prompts using Google's Veo models (Veo 3 includes synchronized audio)
- **Veo Image to Video** - Generate videos from an input image and optional text prompt

**Key Benefits:**
- Support for Gemini 3 Pro Preview and Gemini 2.5 models
- **Veo video generation** with text-to-video and image-to-video (Veo 3 includes audio)
- Each node selects its own model for maximum flexibility
- State-of-the-art reasoning with Gemini 3 Pro and 2.5 Pro
- Image generation with Gemini 2.5 Flash Image models
- Image editing with natural language instructions (1-3 images)
- Simple, straightforward API integration
- Vision capabilities with batch image support
- Flexible safety controls
- Native multi-turn conversation support

**Installation & Documentation:** See [gemini/README.md](gemini/README.md)

### ERPK/Background Removal

Background removal utilities with multiple backend options for different quality/speed/memory tradeoffs.

**Category in ComfyUI:** `ERPK/Background Removal`

#### Nodes

- **Remove Background (rembg)** - ONNX-based with 14+ models including u2net, isnet, birefnet variants. Best for versatility and CPU support.
- **Remove Background (InSPyReNet)** - PyTorch-based via transparent-background. Supports TorchScript JIT for faster inference.
- **Remove Background (BiRefNet)** - HuggingFace transformers integration. Highest quality, supports HR images (2048x2048).

#### Backend Comparison

| Backend | Runtime | Speed | Quality | Memory | License |
|---------|---------|-------|---------|--------|---------|
| **rembg** | ONNX | Fast | Good | Low-Med | MIT |
| **InSPyReNet** | PyTorch | Medium | Very Good | Medium | MIT |
| **BiRefNet** | PyTorch/HF | Slower | Excellent | High | MIT |

#### Available Models

**rembg (14+ models):**
- `u2net` - General purpose (default)
- `u2netp` - Lightweight, faster
- `u2net_human_seg` - Human segmentation
- `u2net_cloth_seg` - Clothing parsing
- `silueta` - Compact u2net (43MB)
- `isnet-general-use` - General purpose ISNet
- `isnet-anime` - Anime characters
- `sam` - Segment Anything Model
- `birefnet-general`, `birefnet-general-lite`, `birefnet-portrait`, `birefnet-dis`, `birefnet-hrsod`, `birefnet-cod`, `birefnet-massive`

**BiRefNet variants:**
- `ZhengPeng7/BiRefNet` - Default
- `ZhengPeng7/BiRefNet_HR` - High resolution (2048x2048)
- `ZhengPeng7/BiRefNet-matting` - Alpha matting
- `ZhengPeng7/BiRefNet_HR-matting` - HR alpha matting
- `ZhengPeng7/BiRefNet-COD` - Camouflaged object detection
- `ZhengPeng7/BiRefNet_512x512` - Fast (lower resolution)

#### Node Outputs

All nodes output:
- `IMAGE` - RGB image (background removed, composited on black)
- `MASK` - Alpha mask for further compositing

#### Features

- Batch processing with progress display
- Alpha matting refinement (rembg only)
- Model caching to avoid reloading
- GPU acceleration where available
- Graceful fallback when dependencies missing

**Installation & Documentation:** See [bgremoval/README.md](bgremoval/README.md)

### ERPK/Apple

Apple ML models integration, currently featuring SHARP for single-image 3D view synthesis.

**Category in ComfyUI:** `ERPK/Apple/SHARP`
**Version:** 2025.12.18

#### SHARP Nodes

SHARP converts a single photograph into a 3D Gaussian splat representation that can be rendered from novel viewpoints.

- **SHARP Predict** - Convert image to 3D Gaussian splat (.ply file)
- **SHARP Render Views** - Render novel views from .ply (CUDA required)
- **SHARP Render Video** - Render orbit video from .ply (CUDA required)

**Key Features:**
- Single-image to 3D in under 1 second on GPU
- Outputs standard .ply Gaussian splat format
- Novel view rendering with customizable camera paths
- Video generation with orbit trajectories

**Installation & Documentation:** See [apple/README.md](apple/README.md)

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

1. Configure API keys for the services you want to use:
   - **WaveSpeed:** See [wavespeed/README.md](wavespeed/README.md#installation)
   - **Claude:** See [claude/README.md](claude/README.md#installation)
   - **Gemini:** See [gemini/README.md](gemini/README.md#installation)
   - **Background Removal:** No API keys required, models download automatically on first use
   - **Apple/SHARP:** No API keys required. Install with: `pip install git+https://github.com/apple/ml-sharp.git`

2. Find nodes under their respective categories: `ERPK/WaveSpeedAI`, `ERPK/Claude`, `ERPK/Gemini`, `ERPK/Background Removal`, and `ERPK/Apple/SHARP`

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
curl -s http://localhost:8188/object_info | jq 'keys' | grep -i -E "(gemini|claude)"
```

## License

MIT License
