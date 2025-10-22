# ComfyUI Custom Nodes - ERPK Collection

A monorepo for ERPK's custom ComfyUI nodes, extending ComfyUI's functionality through integrations with various AI services and APIs.

**Current Version:** 2025.10.0 (CalVer)

## Repository Structure

```
ComfyUI-Custom-Nodes/
├── wavespeed/                     # WaveSpeed AI integration
│   ├── README.md                  # Package documentation
│   ├── nodes.py                   # Core nodes
│   ├── seedream_v4.py             # Text-to-image node
│   ├── seedream_v4_edit.py        # Image editing node
│   └── wavespeed_api/             # API integration layer
└── claude/                        # Claude API integration
    ├── README.md                  # Package documentation
    ├── nodes.py                   # Core nodes
    ├── prompt_enhancer.py         # Prompt enhancement node
    ├── vision_analysis.py         # Image analysis node
    └── claude_api/                # API integration layer
```

## Available Node Packages

### ERPK/WaveSpeedAI

Custom nodes for WaveSpeed AI's image generation and editing APIs.

**Category in ComfyUI:** `ERPK/WaveSpeedAI`
**Version:** 2025.10.0

#### ByteDance Seedream V4 Models

- **Seedream V4** - Text-to-image generation with configurable dimensions up to 4K (0-4096px)
- **Seedream V4 Sequential** - Multi-image generation with cross-image consistency (1-15 images, $0.027/image)
- **Seedream V4 Edit** - AI-powered image editing with text prompts (up to 10 reference images)
- **Seedream V4 Edit Sequential** - Multi-image editing with coherent results (1-15 images, $0.027/image)

#### Qwen Image Models

- **Qwen Image Text-to-Image** - Bilingual text-to-image generation (Chinese/English, max 1536×1536, $0.02/image)
- **Qwen Image Edit** - Single image editing with bilingual prompts (256-1536px, $0.02/image)
- **Qwen Image Edit Plus** - Advanced editing with up to 3 reference images ($0.02/image)

**Installation & Documentation:** See [wavespeed/README.md](wavespeed/README.md)

⚠️ **Note:** For the official WaveSpeed ComfyUI nodes and documentation, see the [official WaveSpeed ComfyUI repository](https://github.com/wavespeedai/ComfyUI-WaveSpeed).

### ERPK/Claude

Claude API integration for text generation, prompt enhancement, vision analysis, and conversational AI.

**Category in ComfyUI:** `ERPK/Claude`
**Version:** 2025.10.0

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

## Installation

Each node package has its own installation instructions. See the individual package README files for details:

**ERPK/WaveSpeedAI:** [Installation Guide](wavespeed/README.md#installation)
**ERPK/Claude:** [Installation Guide](claude/README.md#installation)

### Quick Start

1. Navigate to your ComfyUI custom_nodes directory
2. Clone this repository: `git clone https://github.com/YOUR_USERNAME/ComfyUI-Custom-Nodes ERPK` (or any folder name)
3. Install dependencies for each package:
   - WaveSpeed: `cd ERPK/wavespeed && pip install -r requirements.txt`
   - Claude: `cd ERPK/claude && pip install -r requirements.txt`
4. Configure API keys (see individual package READMEs)
5. Restart ComfyUI
6. Find nodes under their respective categories: `ERPK/WaveSpeedAI` and `ERPK/Claude`

## License

MIT License
