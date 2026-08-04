# OpenAI API Integration for ComfyUI

Complete OpenAI API integration providing text generation, vision analysis, multi-turn conversations, and image generation/editing for ComfyUI workflows.

**Version:** 2026.8.2
**Category in ComfyUI:** `ERPK/OpenAI`

## Features

- **Text Generation** - Use all GPT models (GPT-5.5 + GPT-5.5 Pro premium flagships, GPT-5.4 family, GPT-5.2, GPT-4.1, GPT-4o, o3, o3-mini, o3-pro, o4-mini)
- **Vision Analysis** - Analyze images with GPT-4o / GPT-5 vision capabilities
- **Image Generation** - Generate images with GPT Image 2 (flagship), GPT Image 1.5, and GPT Image 1 / Mini
- **Image Generation (Responses API)** - Orchestrated image generation via a mainline reasoning model with optional web-search grounding
- **Image Editing** - Edit and inpaint images with natural language prompts
- **Multi-turn Conversations** - Maintain chat history across requests
- **System Instructions** - Set persistent instructions to guide model behavior
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
- `model`: gpt-5.6-sol (default), gpt-5.6-terra, gpt-5.6-luna, gpt-5.5, gpt-5.5-pro, gpt-5.4, gpt-5.4-pro, gpt-5.4-mini, gpt-5.4-nano, gpt-5.2, gpt-5.2-pro, gpt-5.1, gpt-5, gpt-5-mini, gpt-5-nano, gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, gpt-4o, gpt-4o-mini, chat-latest, o4-mini, o3, o3-mini, o3-pro
- `temperature`: 0.0-2.0 (creativity level, default: 0.7)
- `max_tokens`: 256-16384 (output length, default: 4096)
- `top_p`: 0.0-1.0 (nucleus sampling, default: 1.0, set <1.0 to enable)
- `stop_sequences`: Newline-separated sequences where generation stops
- `response_format`: Output format - "default" or "json_object"
- `reasoning_effort`: Reasoning depth for reasoning-capable models (gpt-5.5, gpt-5.5-pro, gpt-5.4 family, o3, o4-mini) — none, minimal, low, medium, high, xhigh
- `verbosity`: Output verbosity for gpt-5.x models (gpt-5.5, gpt-5.5-pro, gpt-5.4 family, gpt-5.x family) — default, low, medium, high. Shapes how chatty the response is independently of `max_tokens`. 'default' lets the model pick. Silently dropped for older models.

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
- `model`: gpt-5.6-sol (default), gpt-5.6-terra, gpt-5.6-luna, gpt-5.5, gpt-5.5-pro, gpt-5.4, gpt-5.4-pro, gpt-5.4-mini, gpt-5.4-nano, gpt-5.2, gpt-5.2-pro, gpt-5.1, gpt-5, gpt-5-mini, gpt-5-nano, gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, gpt-4o, gpt-4o-mini, chat-latest, o4-mini, o3, o3-mini, o3-pro
- `chat_session`: Previous chat session (optional, connects from previous chat node)
- `reset_conversation`: Start new conversation (default: false)
- `temperature`: 0.0-2.0 (default: 0.7)
- `max_tokens`: 256-16384 (default: 4096)
- `top_p`: 0.0-1.0 (nucleus sampling, default: 1.0, set <1.0 to enable)
- `stop_sequences`: Newline-separated sequences where generation stops
- `response_format`: Output format - "default" or "json_object"
- `reasoning_effort`: Reasoning depth for reasoning-capable models — none, minimal, low, medium, high, xhigh

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
- `model`: gpt-5.6-sol (default), gpt-5.6-terra, gpt-5.6-luna, gpt-5.5, gpt-5.5-pro, gpt-5.4, gpt-5.4-pro, gpt-5.4-mini, gpt-5.4-nano, gpt-5.2, gpt-5.2-pro, gpt-5.1, gpt-5, gpt-5-mini, gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, gpt-4o, gpt-4o-mini
- `detail`: Image analysis detail level - "auto" (default), "low" (faster/cheaper), "high" (more detailed)
- `max_tokens`: 256-16384 (default: 4096)
- `temperature`: 0.0-2.0 (default: 0.4, lower for more factual)

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
- `model`: gpt-image-2 (default, latest flagship), gpt-image-1.5, gpt-image-1, gpt-image-1-mini
- `size`: Free-form WIDTHxHEIGHT string (default 1024x1024). Each model has its own supported sizes; the API rejects unsupported values.
- `quality`: Image quality - auto (default), low, medium, high (GPT Image family)
- `background`: Background type - auto, transparent, opaque (GPT Image family)
- `n`: Number of images (1-10)

**Outputs:**
- `image`: Generated image batch (ComfyUI IMAGE tensor; when n>1, all images are stacked into a batch)
- `revised_prompt`: Model's revised prompt (GPT Image models may modify your prompt)

**Features:**
- Credentials resolved from ComfyUI Settings, the node input, or config.ini
- Direct image output compatible with all ComfyUI image nodes
- Transparent background support with gpt-image-1.5 / gpt-image-1 / gpt-image-1-mini
- n>1 returns a batched IMAGE tensor — no images are dropped
- Free-form size input (validated against the model's supported sizes by the API)

**gpt-image-2 constraints** (enforced client-side as defense-in-depth):
- Max edge ≤ 3840px, both edges multiples of 16
- Total pixels between 655,360 and 8,294,400
- Aspect ratio (long:short) ≤ 3:1

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
- `mainline_model`: Text/reasoning model that orchestrates the call — gpt-5.6-sol (default), gpt-5.6-terra, gpt-5.6-luna, gpt-5.5 (premium tier), gpt-5.5-pro (extended-compute), gpt-5.4, gpt-5.4-pro, gpt-5.4-mini, gpt-5.4-nano, gpt-5.2, gpt-5.2-pro, gpt-5.1, gpt-5, o3, o4-mini, etc.
- `image_model`: Underlying GPT Image model — gpt-image-2 (default), gpt-image-1.5, gpt-image-1, gpt-image-1-mini
- `reasoning_effort`: none (default), minimal, low, medium, high, xhigh (only reasoning-capable mainlines use this)
- `size`: 1024x1024 (default) and common variants
- `quality`: auto / low / medium / high
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
- `model`: gpt-image-2 (default, latest flagship), gpt-image-1.5, gpt-image-1, gpt-image-1-mini
- `size`: Output image size - 1024x1024 (default), 1024x1536, 1536x1024, 512x512, 256x256
- `quality`: Image quality - auto (default), low, medium, high
- `background`: auto / transparent / opaque (GPT Image family)
- `input_fidelity`: auto / high / low (gpt-image-1.5 / gpt-image-1 / mini; gpt-image-2 always processes at high fidelity and the param is dropped silently)
- `n`: Number of variations (1-4)

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

**Note:** gpt-image-1.5 provides the best editing results. gpt-image-1 also works well.

---

## Model Comparison

### Text Generation Models

| Model | Best For | Context Window | Notes |
|-------|----------|----------------|-------|
| **gpt-5.6-sol** | Current flagship — most complex professional work | — | **Node default**, highest GPT-5.6 capability tier |
| **gpt-5.6-terra** | Balanced GPT-5.6 tier | — | Mid capability/cost |
| **gpt-5.6-luna** | Fast, cost-efficient GPT-5.6 tier | — | Lowest GPT-5.6 cost |
| **gpt-5.5** | Previous premium flagship | 1.05M tokens | $5/$30 per MTok (2x of 5.4); highest reasoning tier; sessions over 272K input billed at 2x input / 1.5x output |
| **gpt-5.5-pro** | Extended-compute premium tier | 1.05M tokens | $30/$180 per MTok (no streaming, no cached input discount); slowest; recommend background mode for long requests |
| **gpt-5.4** | Cost-sensitive flagship alternative | 1M tokens | $2.50/$15 per MTok; configurable reasoning_effort |
| **gpt-5.4-pro** | Extended compute | 1M tokens | Responses API only; highest quality |
| **gpt-5.4-mini** | Fast reasoning | 400K tokens | Cost-efficient flagship tier |
| **gpt-5.4-nano** | Fastest GPT-5.4 | 400K tokens | Lowest cost in flagship family |
| **gpt-5.2** | Coding/agents | 400K tokens | Previous-gen; still strong for engineering |
| **gpt-5.2-pro** | Precision tasks | 400K tokens | Smarter, more precise responses |
| **gpt-5.1** | Coding/agents | 400K tokens | Configurable reasoning effort |
| **gpt-5** | Reasoning | 400K tokens | Earlier flagship reasoning model |
| **gpt-5-mini** | Fast, cost-efficient | 400K tokens | Good balance |
| **gpt-5-nano** | Fastest, lowest cost | 400K tokens | Simple tasks |
| **gpt-4.1** | Non-reasoning tasks | 1M tokens | Smartest non-reasoning model |
| **gpt-4.1-mini** | Fast, cost-effective | 1M tokens | Budget option |
| **gpt-4.1-nano** | Fastest GPT-4.1 | 1M tokens | Lowest cost GPT-4.1 |
| **gpt-4o** | Multimodal (text + vision) | 128K tokens | Cheap, vision-capable fallback |
| **gpt-4o-mini** | Fast multimodal | 128K tokens | Budget vision |
| **o4-mini** | Fast reasoning | 200K tokens | STEM and technical |
| **o3** | Advanced reasoning | 200K tokens | Complex problems |
| **o3-mini** | Cost-efficient reasoning | 200K tokens | Budget STEM |
| **o3-pro** | Most powerful reasoning | 200K tokens | Hardest problems |

### Image Generation Models

| Model | Best For | Notes |
|-------|----------|-------|
| **gpt-image-2** | Latest flagship | **Default**, 4K output, multilingual text, no transparent background |
| **gpt-image-1.5** | Previous flagship | 2K output, transparent background support |
| **gpt-image-1** | High quality | Editing, transparent backgrounds |
| **gpt-image-1-mini** | Cost-efficient | Budget image generation |

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
- Transparent backgrounds are supported by the GPT Image family. Pass-through values: any of `auto`, `transparent`, `opaque` go to the API as-is.
- gpt-image-2 enforces min 655,360 total pixels and max-edge 3840 — the size input is free-form, so type a size your chosen model supports

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
