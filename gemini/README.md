# Gemini API Integration for ComfyUI

Complete Google Gemini API integration providing text generation, vision analysis, multi-turn conversations, image generation, image editing, and safety controls for ComfyUI workflows.

**Version:** 2025.10.0
**Category in ComfyUI:** `ERPK/Gemini`

## Features

- **Text Generation** - Use all Gemini models (2.5 Pro, 2.5 Flash, 2.0 Flash Experimental)
- **Vision Analysis** - Analyze images with Gemini's multimodal capabilities
- **Image Generation** - Generate images from text descriptions
- **Image Editing** - Edit and modify images with natural language prompts (1-3 images)
- **Multi-turn Conversations** - Maintain chat history across requests
- **System Instructions** - Set persistent instructions to guide model behavior
- **Safety Settings** - Configure content safety filters with presets or custom thresholds
- **Full ComfyUI Integration** - Native node types, workflow compatibility

## Installation

### Prerequisites

- ComfyUI installed and running
- Python 3.10 or higher
- Google API key ([get one here](https://aistudio.google.com/app/apikey))

### Steps

1. **Navigate to ComfyUI custom_nodes directory:**
   ```bash
   cd ComfyUI/custom_nodes
   ```

2. **Clone or copy this repository:**
   ```bash
   # If cloning the full repository
   git clone https://github.com/YOUR_USERNAME/ComfyUI-Custom-Nodes ERPK

   # Or just copy the gemini/ folder into custom_nodes/
   ```

3. **Install dependencies:**
   ```bash
   cd ERPK/gemini  # or gemini/ if copied directly
   pip install -r requirements.txt
   ```

4. **Configure API key** (choose one method):

   **Method 1: Environment Variable** (Recommended)
   ```bash
   export GOOGLE_API_KEY="your-api-key-here"
   ```

   **Method 2: config.ini File**
   ```ini
   # Edit gemini/config.ini
   [gemini]
   api_key = your-api-key-here
   ```

   **Method 3: In ComfyUI Node**
   Enter API key directly in the Gemini API Config node

5. **Restart ComfyUI**

6. **Verify installation:**
   - Look for `ERPK/Gemini` category in ComfyUI node menu
   - Should see 8 nodes available

## Available Nodes

### Core Nodes

#### Gemini API Config
Initializes the Gemini API client. Required for all other nodes.

**Inputs:**
- `model`: gemini-2.5-flash (default), gemini-2.5-pro-latest, gemini-2.5-pro, gemini-2.5-flash-latest, gemini-2.5-flash-preview, gemini-2.5-flash-lite, gemini-2.5-flash-lite-preview, gemini-2.0-flash-exp
- `api_key`: Optional API key (uses env/config if empty)

**Outputs:**
- `client`: Gemini API client instance

---

#### Gemini Text Generation
General-purpose text generation and completion.

**Inputs:**
- `client`: Gemini API client
- `prompt`: Text prompt
- `temperature`: 0.0-2.0 (creativity level, default: 0.7)
- `max_tokens`: 256-8192 (output length, default: 8192)

**Outputs:**
- `response`: Generated text

**Example Uses:**
- Text completion and expansion
- Creative writing
- Content generation
- Text transformation

---

#### Gemini Chat
Multi-turn conversation with message history preservation.

**Inputs:**
- `client`: Gemini API client
- `prompt`: Your message
- `chat_session`: Previous chat session (optional, connects from previous chat node)
- `reset_conversation`: Start new conversation (default: false)
- `temperature`: 0.0-2.0 (default: 0.7)
- `max_tokens`: 256-8192 (default: 8192)

**Outputs:**
- `response`: Chat response
- `chat_session`: Updated chat session (connect to next chat node)

**Features:**
- Maintains conversation context automatically
- Connect multiple chat nodes to continue conversations
- Reset conversation to start fresh

---

#### Gemini Vision
Analyze images with questions or instructions.

**Inputs:**
- `client`: Gemini API client
- `image`: ComfyUI image tensor (supports batches)
- `prompt`: Question or instruction about the image(s)
- `max_tokens`: 256-8192 (default: 8192)
- `temperature`: 0.0-2.0 (default: 0.4, lower for more factual)

**Outputs:**
- `analysis`: Text analysis of the image(s)

**Example Uses:**
- Image description and captioning
- Visual question answering
- Object detection and counting
- Scene analysis
- Text extraction from images

---

#### Gemini Image Generation
Generate images from text descriptions using Gemini's image generation models.

**Inputs:**
- `prompt`: Text description of the image to generate
- `api_key`: Optional API key (uses env/config if empty)
- `model`: gemini-2.5-flash-image (recommended) or gemini-2.5-flash-image-preview
- `temperature`: 0.0-2.0 (default: 1.0, higher for more creativity)
- `aspect_ratio`: Image dimensions - "default", "1:1" (square), "9:16" (portrait), "16:9" (landscape), "4:3", "3:4"

**Outputs:**
- `image`: Generated image (ComfyUI IMAGE tensor)

**Features:**
- Standalone node (doesn't need Gemini API Config)
- Direct image output compatible with all ComfyUI image nodes
- Model selector for different image generation models
- Configurable creativity with temperature
- Aspect ratio control for specific dimensions

**Example Prompts:**
- "A futuristic cityscape at sunset with flying cars"
- "A cute robot holding a bouquet of flowers, digital art"
- "Professional photo of a coffee cup on a wooden table, warm lighting"

**Note:** This node generates images, not text. The output is a ComfyUI IMAGE that can be saved, previewed, or processed with other nodes.

---

#### Gemini Image Edit
Edit and modify existing images using text prompts with Gemini's image generation models.

**Inputs:**
- `image`: Input image(s) to edit (ComfyUI IMAGE tensor, supports 1-3 images)
- `prompt`: Text description of how to modify the image(s)
- `api_key`: Optional API key (uses env/config if empty)
- `model`: gemini-2.5-flash-image (recommended) or gemini-2.5-flash-image-preview
- `temperature`: 0.0-2.0 (default: 1.0, higher for more creativity)
- `aspect_ratio`: Image dimensions - "default", "1:1" (square), "9:16" (portrait), "16:9" (landscape), "4:3", "3:4"

**Outputs:**
- `image`: Edited image (ComfyUI IMAGE tensor)

**Features:**
- Standalone node (doesn't need Gemini API Config)
- Supports 1-3 input images for best results (API optimized for this range)
- Image-to-image editing with natural language instructions
- Compatible with all ComfyUI image nodes
- Aspect ratio control for specific output dimensions

**Example Use Cases:**
- "Add a wizard hat to this cat"
- "Change the background to a sunset beach scene"
- "Make the lighting more dramatic and cinematic"
- "Remove the background and replace with solid white"
- "Add raindrops to the window in this image"
- "Combine these two images into a single composition"

**Multi-Image Examples:**
- Provide dress image + model image: "Put the dress from the first image on the person in the second image"
- Provide logo + product image: "Add this logo to the product packaging"
- Provide style reference + content image: "Apply the artistic style from the first image to the second image"

**Note:** Works best with 1-3 images. Using more images may reduce quality or accuracy.

---

#### Gemini System Instruction
Set a system-level instruction to guide model behavior.

**Inputs:**
- `client`: Gemini API client
- `system_instruction`: Instructions to guide the model

**Outputs:**
- `client`: Updated client with system instruction

**Example Instructions:**
- "You are a helpful assistant that responds in JSON format."
- "Always respond in a friendly, casual tone."
- "Focus on technical accuracy and provide code examples."

**Note:** System instructions persist for all subsequent requests with this client.

---

#### Gemini Safety Settings
Configure content safety filters.

**Inputs:**
- `client`: Gemini API client
- `preset`: balanced (default), strict, permissive, or custom
- `harassment`: none/low/medium/high (for custom preset)
- `hate_speech`: none/low/medium/high (for custom preset)
- `sexually_explicit`: none/low/medium/high (for custom preset)
- `dangerous_content`: none/low/medium/high (for custom preset)

**Outputs:**
- `client`: Updated client with safety settings

**Presets:**
- **strict**: Block low and above for all categories (safest)
- **balanced**: Block medium and above (recommended)
- **permissive**: Block only high severity content

---

## Model Comparison

| Model | Best For | Context Window | Notes |
|-------|----------|----------------|-------|
| **gemini-2.5-pro-latest** | Always newest stable Pro | 1M tokens | Auto-updates to latest |
| **gemini-2.5-pro** | Complex reasoning, thinking | 1M tokens | State-of-the-art |
| **gemini-2.5-flash-latest** | Always newest stable Flash | 1M tokens | Auto-updates to latest |
| **gemini-2.5-flash** | Best price-performance | 1M tokens | Recommended default |
| **gemini-2.5-flash-preview** | Latest experimental features | 1M tokens | Preview/experimental |
| **gemini-2.5-flash-image** | Image generation | 1M tokens | ⚠️ Generates images |
| **gemini-2.5-flash-image-preview** | Experimental image gen | 1M tokens | ⚠️ Generates images (preview) |
| **gemini-2.5-flash-lite** | High-speed, cost-efficient | 1M tokens | Fastest, lowest cost |
| **gemini-2.5-flash-lite-preview** | Experimental lite version | 1M tokens | Preview/experimental |
| **gemini-2.0-flash-exp** | Cutting edge 2.0 features | 1M tokens | Experimental |

**Note:** Models marked with ⚠️ generate images instead of text. These require special handling for image output.

## Example Workflows

### Simple Text Generation
```
Gemini API Config → Gemini Text Generation → Output
```

### Multi-turn Conversation
```
Gemini API Config → Gemini Chat → Gemini Chat → Gemini Chat → Output
                         ↓              ↓              ↓
                    (chat_session) (chat_session) (chat_session)
```

### Image Analysis
```
Load Image → Gemini API Config → Gemini Vision → Output
```

### Guided Generation with Safety
```
Gemini API Config → Gemini System Instruction → Gemini Safety Settings → Gemini Text Generation
```

## API Keys and Pricing

### Getting an API Key
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and configure it using one of the methods above

### Pricing
Gemini API offers generous free tier quotas. For current pricing, see:
https://ai.google.dev/pricing

## Troubleshooting

### "No API key found" error
- Verify your API key is set via environment variable, config.ini, or the node input
- Check that the config.ini file has the correct format
- Restart ComfyUI after setting environment variables

### "Response blocked by safety filters" error
- Your prompt or the model's response triggered safety filters
- Try using the Gemini Safety Settings node to adjust thresholds
- Rephrase your prompt to be less ambiguous

### Import errors
- Ensure you've installed dependencies: `pip install -r requirements.txt`
- Check that you're using Python 3.10 or higher
- Restart ComfyUI after installing dependencies

### Model not available
- Some models (like gemini-2.0-flash-exp) are experimental and may have limited availability
- Try using gemini-1.5-flash or gemini-1.5-pro instead

## Support

For issues, feature requests, or questions:
- Open an issue on GitHub
- Check the [Gemini API documentation](https://ai.google.dev/docs)

## License

See the main repository LICENSE file for details.
