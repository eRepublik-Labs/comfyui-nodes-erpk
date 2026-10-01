# OpenAI API Integration for ComfyUI

Complete OpenAI API integration providing text generation, vision analysis, multi-turn conversations, and image generation/editing for ComfyUI workflows.

**Version:** 2026.9.11
**Category in ComfyUI:** `ERPK/OpenAI`

## Features

- **Text Generation** - GPT-6.1 Sol (default), the GPT-6 Astra/Sol/Luna and GPT-5.6 Sol/Terra/Luna tiers, and chat-latest
- **Vision Analysis** - Analyze images with any of the text models (all accept image input)
- **Image Generation** - Generate images with GPT Image 2 and GPT Image 2.5 Sunburst / Flare
- **Image Generation (Responses API)** - Orchestrated image generation via a mainline reasoning model with optional web-search grounding
- **Image Editing** - Edit and inpaint images with natural language prompts
- **Multi-turn Conversations** - Maintain chat history across requests
- **System Instructions** - Set persistent instructions to guide model behavior (text, chat, vision and Image via Responses; the direct image endpoints take a prompt only)
- **Full ComfyUI Integration** - Native node types, workflow compatibility

## Installation

### Prerequisites

- ComfyUI installed and running
- Python 3.10 or higher
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### Steps

1. **Navigate to ComfyUI custom_nodes directory:**
   ```bash
   cd /path/to/ComfyUI/custom_nodes/
   ```

2. **Clone the repository as 'erpk':**
   ```bash
   git clone https://github.com/eRepublik-Labs/comfyui-nodes-erpk.git erpk
   ```

3. **Install dependencies:**
   ```bash
   cd erpk
   pip install -r requirements.txt
   ```

4. **Configure API key** (choose one method — checked in priority order, highest first):

   **Method 1: ComfyUI Settings** (Recommended — highest priority)
   Go to **Settings > ERPK > API Keys** and enter your OpenAI API key. You can also access this via right-click canvas > **ERPK Settings**.
   Keys configured here are stored in your user settings, not in workflows, so they won't leak when sharing.
   In multi-user installations, each user's keys are resolved separately.

   **Method 2: In ComfyUI Node**
   Enter API key directly in the OpenAI API Config node (not recommended for shared workflows)

   **Method 3: config.ini File** (lowest priority)
   ```ini
   # Edit openai/config.ini
   [openai]
   # api_key = YOUR_OPENAI_API_KEY_HERE
   ```

5. **Restart ComfyUI**

6. **Verify installation:**
   - Look for `ERPK/OpenAI` category in ComfyUI node menu
   - Should see 8 nodes available

## Available Nodes

### Core Nodes

#### OpenAI API Config
Initializes the OpenAI API client. Optional if API key is configured in ComfyUI Settings — generation nodes can run standalone.

**Inputs:**
- `api_key`: Optional API key (uses Settings/config if empty)

**Outputs:**
- `client`: OpenAI API client instance

---

#### OpenAI Text Generation
General-purpose text generation and completion.

**Inputs:**
- `client`: OpenAI API client
- `prompt`: Text prompt
- `model`: gpt-6.1-sol (default), gpt-6-astra, gpt-6-sol, gpt-6-luna, gpt-5.6-sol, gpt-5.6-terra, gpt-5.6-luna, chat-latest
- `temperature`: 0.0-2.0 (creativity level, default: 0.7; ignored by every current model, which accepts only the default)
- `max_tokens`: 256-128000 (output length, default: 4096)
- `top_p`: 0.0-1.0 (nucleus sampling, default: 1.0; ignored by every current model, which accepts only the default)
- `stop_sequences`: Newline-separated sequences where generation stops (ignored by every current model, which accepts only the default)
- `response_format`: Output format - "default" or "json_object"
- `reasoning_effort`: Reasoning depth for the gpt-6.x and gpt-5.6 models — none, minimal, low, medium, high, xhigh. `none` sends no effort (model default); `minimal` is rejected by every current model and is sent as `low`. Dropped for chat-latest
- `verbosity`: Output verbosity for the gpt-6.x and gpt-5.6 models — default, low, medium, high. Shapes how chatty the response is independently of `max_tokens`. 'default' lets the model pick. Dropped for chat-latest.

**Outputs:**
- `response`: Generated text

**Example Uses:**
- Text completion and expansion
- Creative writing
- Content generation
- Text transformation
- **JSON mode**: Set response_format to "json_object" for structured data extraction

---

#### OpenAI Chat
Multi-turn conversation with message history preservation.

**Inputs:**
- `client`: OpenAI API client
- `prompt`: Your message
- `model`: gpt-6.1-sol (default), gpt-6-astra, gpt-6-sol, gpt-6-luna, gpt-5.6-sol, gpt-5.6-terra, gpt-5.6-luna, chat-latest
- `chat_session`: Previous chat session (optional, connects from previous chat node)
- `reset_conversation`: Start new conversation (default: false)
- `temperature`: 0.0-2.0 (default: 0.7; ignored by every current model, which accepts only the default)
- `max_tokens`: 256-128000 (default: 4096)
- `top_p`: 0.0-1.0 (nucleus sampling, default: 1.0; ignored by every current model, which accepts only the default)
- `stop_sequences`: Newline-separated sequences where generation stops (ignored by every current model, which accepts only the default)
- `response_format`: Output format - "default" or "json_object"
- `reasoning_effort`: Reasoning depth for the gpt-6.x and gpt-5.6 models — none, minimal, low, medium, high, xhigh (`minimal` is sent as `low`)

**Outputs:**
- `response`: Chat response
- `chat_session`: Updated chat session (connect to next chat node)

**Features:**
- Maintains conversation context automatically
- Connect multiple chat nodes to continue conversations
- Reset conversation to start fresh
- Supports JSON mode for structured responses in conversations

---

#### OpenAI Vision
Analyze images with questions or instructions.

**Inputs:**
- `client`: OpenAI API client
- `image`: ComfyUI image tensor (supports batches)
- `prompt`: Question or instruction about the image(s)
- `model`: gpt-6.1-sol (default), gpt-6-astra, gpt-6-sol, gpt-6-luna, gpt-5.6-sol, gpt-5.6-terra, gpt-5.6-luna, chat-latest
- `detail`: Image analysis detail level - "auto" (default), "low" (faster/cheaper), "high" (more detailed)
- `max_tokens`: 256-128000 (default: 4096)
- `temperature`: 0.0-2.0 (default: 0.4; ignored by every current model, which accepts only the default)

**Outputs:**
- `analysis`: Text analysis of the image(s)

**Example Uses:**
- Image description and captioning
- Visual question answering
- Object detection and counting
- Scene analysis
- Text extraction from images (OCR)
- Document understanding

---

#### OpenAI System Instruction
Set a system-level instruction to guide model behavior.

**Inputs:**
- `client`: OpenAI API client
- `system_instruction`: Instructions to guide the model

**Outputs:**
- `client`: Updated client with system instruction

**Example Instructions:**
- "You are a helpful assistant that responds in JSON format."
- "Always respond in a friendly, casual tone."
- "Focus on technical accuracy and provide code examples."

**Note:** System instructions persist for all subsequent requests with this client.

---

### Image Nodes

#### OpenAI Image Generation
Generate images from text descriptions using OpenAI's image generation models.

**Inputs:**
- `prompt`: Text description of the image to generate
- `client`: Optional OpenAI API client (from OpenAI API Config node)
- `model`: gpt-image-2 (default), gpt-image-2.5-sunburst, gpt-image-2.5-flare
- `size`: Preset (auto, 1024x1024, 1024x1536, 1536x1024, 2048x2048, 2048x1152, 1152x2048, 3840x2160, 2160x3840) or Custom
- `custom_width` / `custom_height`: Used when size is Custom (256 to 3840, step 16). Sizes outside the gpt-image-2 envelope below are rejected before the request is sent.
- `quality`: Image quality - auto (default), low, medium, high, xhigh, max (xhigh/max on GPT Image 2.5 only, clamped to high on gpt-image-2)
- `background`: Background type - auto, transparent, opaque (transparent: GPT Image 2.5 only; gpt-image-2 rejects it)
- `moderation`: auto (default) / low
- `n`: Number of images (1-10)
- `seed`: Cache control only, not sent to the API (-1 randomizes)
- `output_format`: png (default), jpeg, webp
- `output_compression`: 0-100 (default 100), sent only with jpeg or webp

**Outputs:**
- `image`: Generated image batch (ComfyUI IMAGE tensor; when n>1, all images are stacked into a batch)
- `revised_prompt`: Model's revised prompt (GPT Image models may modify your prompt)

**Features:**
- Credentials resolved from ComfyUI Settings, the node input, or config.ini
- Direct image output compatible with all ComfyUI image nodes
- Transparent background support on gpt-image-2.5-sunburst / gpt-image-2.5-flare (in preview on gpt-image-2)
- n>1 returns a batched IMAGE tensor — no images are dropped
- Size presets plus a Custom width/height pair (validated against the model's supported sizes by the API)

**gpt-image-2 and 2.5 constraints** (enforced client-side as defense-in-depth):
- Max edge ≤ 3840px, both edges multiples of 16
- Total pixels between 655,360 and 8,294,400
- Aspect ratio (long:short) ≤ 3:1
- Resolutions above 2560x1440 (up to 3840x2160) are accepted but marked experimental by OpenAI

**Example Prompts:**
- "A futuristic cityscape at sunset with flying cars"
- "A cute robot holding a bouquet of flowers, digital art"
- "Professional photo of a coffee cup on a wooden table, warm lighting"

---

#### OpenAI Image Generation (Responses)
Generate images via the OpenAI Responses API with a mainline reasoning model driving the `image_generation` hosted tool. Unlike the direct `/v1/images/generations` endpoint, this routes through `/v1/responses` so the mainline model can revise your prompt, reason about composition, and optionally invoke web search before producing the image.

**Inputs:**
- `prompt`: Image description (the mainline model may auto-revise before dispatch)
- `client`: Optional OpenAI API client
- `mainline_model`: Text/reasoning model that orchestrates the call — gpt-6.1-sol (default), gpt-6-astra, gpt-6-sol, gpt-6-luna, gpt-5.6-sol, gpt-5.6-terra, gpt-5.6-luna
- `image_model`: Underlying GPT Image model — gpt-image-2 (default), gpt-image-2.5-sunburst, gpt-image-2.5-flare
- `reasoning_effort`: none (default), minimal, low, medium, high, xhigh (`minimal` is rejected alongside the image tool and is sent as `low`)
- `size`: 1024x1024 (default) and common variants
- `quality`: auto / low / medium / high / xhigh / max (xhigh/max on GPT Image 2.5 only)
- `background`: auto / transparent / opaque
- `output_format`: png (default), jpeg, webp
- `moderation`: auto (default) or low
- `enable_web_search`: Attach the `web_search` tool so the mainline model can ground the prompt in fresh reference material (adds ~$10/1000 calls when invoked)
- `seed`: Cache-bust seed (randomizes by default)

**Outputs:**
- `image`: Generated image(s) as an IMAGE tensor (multi-image responses are batched)
- `revised_prompt`: Prompt after mainline-model revision
- `reasoning_summary`: Raw chain-of-thought from the mainline when reasoning is enabled. **Heads up:** this mixes creative rationale with orchestration-level thinking (output channels, tool-call structure). Ignore the output if you only want the image.

**When to use this vs. OpenAI Image Generation:**
- Use **OpenAI Image Generation (Responses)** when you want mainline reasoning, prompt revision, or web-search grounding before the image.
- Use **OpenAI Image Generation** for a direct, lower-cost call to the image endpoint with no reasoning step.

---

#### OpenAI Image Edit
Edit and modify existing images using text prompts with optional masking.

**Inputs:**
- `image`: Input image to edit (ComfyUI IMAGE tensor)
- `prompt`: Text description of how to modify the image
- `client`: Optional OpenAI API client (from OpenAI API Config node)
- `mask`: Optional mask (ComfyUI MASK tensor) - white areas will be edited
- `model`: gpt-image-2 (default), gpt-image-2.5-sunburst, gpt-image-2.5-flare
- `size`: Preset (auto, 1024x1024, 1024x1536, 1536x1024, 2048x2048, 2048x1152, 1152x2048, 3840x2160, 2160x3840) or Custom. Every model accepts any Custom size within the gpt-image-2 constraints listed under OpenAI Image Generation
- `custom_width` / `custom_height`: Used when size is Custom (256 to 3840, step 16)
- `quality`: Image quality - auto (default), low, medium, high, xhigh, max (xhigh/max on GPT Image 2.5 only)
- `moderation`: auto (default) / low
- `background`: auto / transparent / opaque (transparent: GPT Image 2.5 only; gpt-image-2 rejects it)
- `input_fidelity`: auto / high / low (ignored by every current model: gpt-image-2 and the 2.5 models reject the param, so it is never sent)
- `n`: Number of variations (1-10)
- `seed`: Cache control only, not sent to the API (-1 randomizes)
- `output_format`: png (default), jpeg, webp
- `output_compression`: 0-100 (default 100), sent only with jpeg or webp

**Outputs:**
- `image`: Edited image (ComfyUI IMAGE tensor)

**Features:**
- Inpainting with optional mask support
- Credentials resolved from ComfyUI Settings, the node input, or config.ini
- Compatible with all ComfyUI image nodes

**Example Use Cases:**
- "Add a wizard hat to this cat"
- "Change the background to a sunset beach scene"
- "Remove the person and fill with background"
- "Add raindrops to the window"

**Note:** gpt-image-2.5-sunburst is the highest-quality editing tier; gpt-image-2.5-flare is the fastest.

---

## Model Comparison

### Text Generation Models

| Model | Best For | Context Window | Notes |
|-------|----------|----------------|-------|
| **gpt-6.1-sol** | Current flagship | 1.05M tokens | **Node default**; 128K output; $2/$10 per MTok ($0.10 cached input) |
| **gpt-6-astra** | Top tier | 1.05M tokens | $10/$50 per MTok |
| **gpt-6-sol** | GPT-6 flagship tier | 1.05M tokens | $2/$10 per MTok |
| **gpt-6-luna** | Most efficient GPT-6 tier | 1.05M tokens | $0.10/$0.50 per MTok |
| **gpt-5.6-sol** | Highest GPT-5.6 capability tier | — | |
| **gpt-5.6-terra** | Balanced GPT-5.6 tier | — | Mid capability/cost |
| **gpt-5.6-luna** | Fast, cost-efficient GPT-5.6 tier | — | Lowest GPT-5.6 cost |
| **chat-latest** | ChatGPT Instant, non-reasoning | 400K tokens | $5/$30 per MTok; no reasoning_effort or verbosity |

Removed on 2026-10-01: gpt-5.5, gpt-5.5-pro, gpt-5.4 / -pro / -mini / -nano, gpt-5.2, gpt-5.2-pro, gpt-5.1, gpt-5 / -mini / -nano, gpt-4.1 / -mini / -nano, gpt-4o, gpt-4o-mini, o4-mini, o3, o3-mini, o3-pro. gpt-5.2-pro, gpt-5.4-pro and gpt-5.5-pro never worked here: they 404 on chat.completions. Every kept model rejects temperature, top_p and stop, so the node no longer sends them.

### Image Generation Models

| Model | Best For | Notes |
|-------|----------|-------|
| **gpt-image-2.5-sunburst** | Highest quality | 4K output, `xhigh`/`max` quality tiers, transparent background |
| **gpt-image-2.5-flare** | Fastest 2.5 tier | 4K output, `xhigh`/`max` quality tiers, transparent background |
| **gpt-image-2** | 4K, multilingual text | **Default**, 4K output, multilingual text, transparent background in preview |

gpt-image-1.5, gpt-image-1 and gpt-image-1-mini were removed on 2026-10-01, along with the DALL-E-only quality values hd / standard.

## Example Workflows

> **Note:** The OpenAI API Config node is optional when your API key is configured in ComfyUI Settings. Nodes can run standalone without it.

### Simple Text Generation
```
OpenAI API Config → OpenAI Text Generation → Output
```

### Multi-turn Conversation
```
OpenAI API Config → OpenAI Chat → OpenAI Chat → OpenAI Chat → Output
                         ↓              ↓              ↓
                    (chat_session) (chat_session) (chat_session)
```

### Image Analysis
```
Load Image → OpenAI API Config → OpenAI Vision → Output
```

### Guided Generation
```
OpenAI API Config → OpenAI System Instruction → OpenAI Text Generation → Output
```

### Image Generation
```
OpenAI API Config → OpenAI Image Generation → Save Image
```

### Image Generation with Reasoning (Responses API)
```
OpenAI API Config → OpenAI Image Generation (Responses) → Save Image
```
Use this variant when you want the mainline model to revise the prompt, reason about composition, or invoke web search before the image is generated.

### Image Editing with Mask
```
Load Image → OpenAI API Config → OpenAI Image Edit → Save Image
Load Mask  ↗
```

## API Keys and Pricing

### Getting an API Key
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key and configure it using one of the methods above

### Pricing
For current pricing, see:
https://openai.com/pricing

## Troubleshooting

### "No API key found" error
- The API key is resolved in this priority order: ComfyUI Settings > node widget > config.ini
- Set your API key via ComfyUI Settings (**Settings > ERPK > API Keys**, recommended) or right-click canvas > **ERPK Settings**
- Or verify your API key is set via config.ini or the node input
- Check that the config.ini file has the correct format

### "Content policy violation" error
- Your prompt or the model's response triggered content filters
- Rephrase your prompt to be less ambiguous
- OpenAI has stricter content policies than some other providers

### Import errors
- Ensure you've installed dependencies: `pip install -r requirements.txt`
- Check that you're using Python 3.10 or higher
- Restart ComfyUI after installing dependencies

### Image generation fails
- Check your API quota and billing status
- Some sizes are only available for certain models
- Transparent backgrounds are supported on GPT Image 2.5 and in preview on gpt-image-2. Pass-through values: any of `auto`, `transparent`, `opaque` go to the API as-is. Transparent needs png or webp output.
- gpt-image-2 enforces min 655,360 total pixels and max-edge 3840 — pick Custom and type a size your chosen model supports

### Rate limiting
- The nodes include automatic retry with exponential backoff
- If you hit rate limits frequently, consider upgrading your API tier
- Add delays between requests in your workflow

## Support

For issues, feature requests, or questions:
- Open an issue on GitHub
- Check the [OpenAI API documentation](https://platform.openai.com/docs)

## License

See the main repository LICENSE file for details.
