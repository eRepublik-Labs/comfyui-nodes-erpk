# OpenAI API Integration for ComfyUI

Complete OpenAI API integration providing text generation, vision analysis, multi-turn conversations, and image generation/editing for ComfyUI workflows.

**Version:** 2026.1.18
**Category in ComfyUI:** `ERPK/OpenAI`

## Features

- **Text Generation** - Use all GPT models (GPT-5.2, GPT-4.1, GPT-4o, o3)
- **Vision Analysis** - Analyze images with GPT-4 vision capabilities
- **Image Generation** - Generate images with GPT-Image-1 and DALL-E models
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

4. **Configure API key** (choose one method):

   **Method 1: Environment Variable** (Recommended)
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

   **Method 2: config.ini File**
   ```ini
   # Edit openai/config.ini
   [openai]
   api_key = your-api-key-here
   ```

   **Method 3: In ComfyUI Node**
   Enter API key directly in the OpenAI API Config node

5. **Restart ComfyUI**

6. **Verify installation:**
   - Look for `ERPK/OpenAI` category in ComfyUI node menu
   - Should see 7 nodes available

## Available Nodes

### Core Nodes

#### OpenAI API Config
Initializes the OpenAI API client. Required for all other nodes.

**Inputs:**
- `api_key`: Optional API key (uses env/config if empty)

**Outputs:**
- `client`: OpenAI API client instance

---

#### OpenAI Text Generation
General-purpose text generation and completion.

**Inputs:**
- `client`: OpenAI API client
- `prompt`: Text prompt
- `model`: gpt-4o (default), gpt-5.2, gpt-5.2-pro, gpt-5.1, gpt-5, gpt-5-mini, gpt-5-nano, gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, gpt-4o-mini, o4-mini, o3
- `temperature`: 0.0-2.0 (creativity level, default: 0.7)
- `max_tokens`: 256-16384 (output length, default: 4096)
- `top_p`: 0.0-1.0 (nucleus sampling, default: 1.0, set <1.0 to enable)
- `stop_sequences`: Newline-separated sequences where generation stops
- `response_format`: Output format - "default" or "json_object"

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
- `model`: gpt-4o (default), gpt-5.2, gpt-5.2-pro, gpt-5.1, gpt-5, gpt-5-mini, gpt-5-nano, gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, gpt-4o-mini, o4-mini, o3
- `chat_session`: Previous chat session (optional, connects from previous chat node)
- `reset_conversation`: Start new conversation (default: false)
- `temperature`: 0.0-2.0 (default: 0.7)
- `max_tokens`: 256-16384 (default: 4096)
- `top_p`: 0.0-1.0 (nucleus sampling, default: 1.0, set <1.0 to enable)
- `stop_sequences`: Newline-separated sequences where generation stops
- `response_format`: Output format - "default" or "json_object"

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
- `model`: gpt-5.2 (default), gpt-5.2-pro, gpt-5.1, gpt-5, gpt-5-mini, gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, gpt-4o, gpt-4o-mini
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
- `model`: gpt-image-1.5 (default, best quality), gpt-image-1, gpt-image-1-mini, dall-e-3 (deprecated)
- `size`: Image dimensions - 1024x1024 (default), 1024x1536, 1536x1024, 512x512, 256x256, 1792x1024, 1024x1792
- `quality`: Image quality - auto (default), low, medium, high (gpt-image-1) or hd, standard (dall-e-3)
- `background`: Background type - auto, transparent, opaque (gpt-image-1 only)
- `n`: Number of images (1-4, dall-e-3 only supports 1)
- `api_key`: Optional API key (only needed if not using client input)

**Outputs:**
- `image`: Generated image (ComfyUI IMAGE tensor)
- `revised_prompt`: Model's revised prompt (DALL-E 3 may modify your prompt)

**Features:**
- Works with OpenAI API Config node or standalone with API key
- Direct image output compatible with all ComfyUI image nodes
- Transparent background support with gpt-image-1
- Multiple size options

**Example Prompts:**
- "A futuristic cityscape at sunset with flying cars"
- "A cute robot holding a bouquet of flowers, digital art"
- "Professional photo of a coffee cup on a wooden table, warm lighting"

---

#### OpenAI Image Edit
Edit and modify existing images using text prompts with optional masking.

**Inputs:**
- `image`: Input image to edit (ComfyUI IMAGE tensor)
- `prompt`: Text description of how to modify the image
- `client`: Optional OpenAI API client (from OpenAI API Config node)
- `mask`: Optional mask (ComfyUI MASK tensor) - white areas will be edited
- `model`: gpt-image-1.5 (default, recommended), gpt-image-1, gpt-image-1-mini
- `size`: Output image size - 1024x1024 (default), 1024x1536, 1536x1024, 512x512, 256x256
- `quality`: Image quality - auto (default), low, medium, high (gpt-image-1 only)
- `n`: Number of variations (1-4)
- `api_key`: Optional API key (only needed if not using client input)

**Outputs:**
- `image`: Edited image (ComfyUI IMAGE tensor)

**Features:**
- Inpainting with optional mask support
- Works with OpenAI API Config node or standalone with API key
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
| **gpt-5.2** | Latest flagship | 400K tokens | Best for coding/agents |
| **gpt-5.2-pro** | Precision tasks | 400K tokens | Smarter, more precise responses |
| **gpt-5.1** | Coding/agents | 400K tokens | Configurable reasoning effort |
| **gpt-5** | Reasoning | 400K tokens | Previous flagship reasoning model |
| **gpt-5-mini** | Fast, cost-efficient | 400K tokens | Good balance |
| **gpt-5-nano** | Fastest, lowest cost | 400K tokens | Simple tasks |
| **gpt-4.1** | Non-reasoning tasks | 1M tokens | Smartest non-reasoning model |
| **gpt-4.1-mini** | Fast, cost-effective | 1M tokens | Budget option |
| **gpt-4.1-nano** | Fastest GPT-4.1 | 1M tokens | Lowest cost GPT-4.1 |
| **gpt-4o** | Multimodal (text + vision) | 128K tokens | **Default**, great for vision |
| **gpt-4o-mini** | Fast multimodal | 128K tokens | Budget vision |
| **o4-mini** | Fast reasoning | 200K tokens | STEM and technical |
| **o3** | Advanced reasoning | 200K tokens | Complex problems |

### Image Generation Models

| Model | Best For | Notes |
|-------|----------|-------|
| **gpt-image-1.5** | Highest quality | **Default**, latest model, best editing |
| **gpt-image-1** | High quality | Editing, transparent backgrounds |
| **gpt-image-1-mini** | Cost-efficient | Budget image generation |
| **dall-e-3** | Legacy generation | Deprecated |

## Example Workflows

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
- Verify your API key is set via environment variable, config.ini, or the node input
- Check that the config.ini file has the correct format
- Restart ComfyUI after setting environment variables

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
- Transparent backgrounds only work with gpt-image-1

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
