# Gemini API Integration for ComfyUI

Complete Google Gemini API integration providing text generation, vision analysis, multi-turn conversations, image generation, image editing, **video generation (Veo)**, and safety controls for ComfyUI workflows.

**Version:** 2026.1.21
**Category in ComfyUI:** `ERPK/Gemini` and `ERPK/Gemini/Veo`

## Features

- **Text Generation** - Use all Gemini models (3 Pro, 3 Flash, 2.5 Pro, 2.5 Flash)
- **Vision Analysis** - Analyze images with Gemini's multimodal capabilities
- **Image Generation** - Generate images from text descriptions
- **Image Editing** - Edit and modify images with natural language prompts (up to 14 reference images)
- **Video Generation (Veo)** - Generate videos from text or images using Google's Veo models
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
   cd /path/to/ComfyUI/custom_nodes/
   ```

2. **Clone the repository as 'erpk':**
   ```bash
   git clone https://github.com/eRepublik-Labs/comfyui-nodes-erpk.git erpk
   ```

3. **Install dependencies:**
   ```bash
   cd erpk
   pip install -r gemini/requirements.txt
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
   - Look for `ERPK/Gemini` and `ERPK/Gemini/Veo` categories in ComfyUI node menu
   - Should see 10 nodes available (8 Gemini + 2 Veo)

## Available Nodes

### Core Nodes

#### Gemini API Config
Initializes the Gemini API client. Required for all other nodes.

**Inputs:**
- `api_key`: Optional API key (uses env/config if empty)

**Outputs:**
- `client`: Gemini API client instance

---

#### Gemini Text Generation
General-purpose text generation and completion.

**Inputs:**
- `client`: Gemini API client
- `prompt`: Text prompt
- `model`: gemini-2.5-flash (default), gemini-3-pro-preview, gemini-3-flash-preview, gemini-2.5-pro, gemini-2.5-flash-lite
- `temperature`: 0.0-2.0 (creativity level, default: 0.7)
- `max_tokens`: 256-8192 (output length, default: 8192)
- `top_p`: 0.0-1.0 (nucleus sampling, default: 0.95, set 0.0 to disable)
- `top_k`: 0-100 (top-k sampling, default: 40, set 0 to disable)
- `stop_sequences`: Newline-separated sequences where generation stops
- `response_mime_type`: Output format - "default", "text/plain", or "application/json"
- `response_schema`: JSON schema for structured output (used with application/json)

**Outputs:**
- `response`: Generated text

**Example Uses:**
- Text completion and expansion
- Creative writing
- Content generation
- Text transformation
- **JSON mode**: Set response_mime_type to "application/json" for structured data extraction

---

#### Gemini Chat
Multi-turn conversation with message history preservation.

**Inputs:**
- `client`: Gemini API client
- `prompt`: Your message
- `model`: gemini-2.5-flash (default), gemini-3-pro-preview, gemini-3-flash-preview, gemini-2.5-pro, gemini-2.5-flash-lite
- `chat_session`: Previous chat session (optional, connects from previous chat node)
- `reset_conversation`: Start new conversation (default: false)
- `temperature`: 0.0-2.0 (default: 0.7)
- `max_tokens`: 256-8192 (default: 8192)
- `top_p`: 0.0-1.0 (nucleus sampling, default: 0.95, set 0.0 to disable)
- `top_k`: 0-100 (top-k sampling, default: 40, set 0 to disable)
- `stop_sequences`: Newline-separated sequences where generation stops
- `response_mime_type`: Output format - "default", "text/plain", or "application/json"
- `response_schema`: JSON schema for structured output (used with application/json)

**Outputs:**
- `response`: Chat response
- `chat_session`: Updated chat session (connect to next chat node)

**Features:**
- Maintains conversation context automatically
- Connect multiple chat nodes to continue conversations
- Reset conversation to start fresh
- Supports JSON mode for structured responses in conversations

---

#### Gemini Vision
Analyze images with questions or instructions.

**Inputs:**
- `client`: Gemini API client
- `image`: ComfyUI image tensor (supports batches)
- `prompt`: Question or instruction about the image(s)
- `model`: gemini-2.5-flash (default), gemini-3-pro-preview, gemini-3-flash-preview, gemini-2.5-pro, gemini-2.5-flash-lite
- `max_tokens`: 256-8192 (default: 8192)
- `temperature`: 0.0-2.0 (default: 0.4, lower for more factual)
- `top_p`: 0.0-1.0 (nucleus sampling, default: 0.95, set 0.0 to disable)
- `top_k`: 0-100 (top-k sampling, default: 40, set 0 to disable)
- `stop_sequences`: Newline-separated sequences where generation stops
- `response_mime_type`: Output format - "default", "text/plain", or "application/json"
- `response_schema`: JSON schema for structured output (used with application/json)

**Outputs:**
- `analysis`: Text analysis of the image(s)

**Example Uses:**
- Image description and captioning
- Visual question answering
- Object detection and counting
- Scene analysis
- Text extraction from images
- **Structured extraction**: Use JSON mode to extract structured data from images (e.g., product info, receipts, forms)

---

#### Gemini Image Generation
Generate images from text descriptions using Gemini's image generation models.

**Inputs:**
- `prompt`: Text description of the image to generate
- `client`: Optional Gemini API client (from Gemini API Config node)
- `model`: gemini-2.5-flash-image (fast, recommended) or gemini-3-pro-image-preview (best quality)
- `temperature`: 0.0-2.0 (default: 1.0, higher for more creativity)
- `aspect_ratio`: Image dimensions - "default", "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"
- `image_size`: Resolution - "default", "1K", "2K", "4K" (only for gemini-3-pro-image-preview, 2.5-flash always 1024px)
- `response_modalities`: "IMAGE" (image only) or "TEXT+IMAGE" (image + text description)
- `enable_google_search`: Enable Google Search grounding (only for gemini-3-pro-image-preview)
- `api_key`: Optional API key (only needed if not using client input)

**Outputs:**
- `image`: Generated image (ComfyUI IMAGE tensor)
- `description`: Text description (only when response_modalities is TEXT+IMAGE)

**Features:**
- Works with Gemini API Config node or standalone with API key
- Direct image output compatible with all ComfyUI image nodes
- Model selector for different image generation models
- Configurable creativity with temperature
- Full aspect ratio support (10 options)
- Resolution control with gemini-3-pro (1K/2K/4K)
- Google Search grounding for factually accurate images

**Example Prompts:**
- "A futuristic cityscape at sunset with flying cars"
- "A cute robot holding a bouquet of flowers, digital art"
- "Professional photo of a coffee cup on a wooden table, warm lighting"

**Note:** This node generates images, not text. The output is a ComfyUI IMAGE that can be saved, previewed, or processed with other nodes.

---

#### Gemini Image Edit
Edit and modify existing images using text prompts with Gemini's image generation models.

**Inputs:**
- `image`: Input image(s) to edit (ComfyUI IMAGE tensor, up to 14 reference images)
- `prompt`: Text description of how to modify the image(s)
- `client`: Optional Gemini API client (from Gemini API Config node)
- `model`: gemini-2.5-flash-image (fast, recommended) or gemini-3-pro-image-preview (best quality)
- `temperature`: 0.0-2.0 (default: 1.0, higher for more creativity)
- `aspect_ratio`: Image dimensions - "default", "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"
- `image_size`: Resolution - "default", "1K", "2K", "4K" (only for gemini-3-pro-image-preview, 2.5-flash always 1024px)
- `response_modalities`: "IMAGE" (image only) or "TEXT+IMAGE" (image + text description)
- `enable_google_search`: Enable Google Search grounding (only for gemini-3-pro-image-preview)
- `api_key`: Optional API key (only needed if not using client input)

**Outputs:**
- `image`: Edited image (ComfyUI IMAGE tensor)
- `description`: Text description (only when response_modalities is TEXT+IMAGE)

**Features:**
- Works with Gemini API Config node or standalone with API key
- Gemini 3 Pro supports up to 14 reference images (up to 6 objects, up to 5 humans)
- Image-to-image editing with natural language instructions
- Compatible with all ComfyUI image nodes
- Full aspect ratio support (10 options)
- Resolution control with gemini-3-pro (1K/2K/4K)
- Google Search grounding for factual accuracy in edits

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

**Note:** Gemini 3 Pro Image supports up to 14 reference images (up to 6 objects, up to 5 humans for character consistency).

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

### Veo Video Generation Nodes

#### Veo Text to Video
Generate videos from text prompts using Google's Veo models.

**Inputs:**
- `client`: Gemini API client (from Gemini API Config node)
- `prompt`: Text description of the video to generate (max 2500 characters)
- `model`: veo-3.1-generate-preview (default, includes audio), veo-3.0-generate-001, or veo-2.0-generate-001
- `aspect_ratio`: 16:9 (landscape) or 9:16 (portrait)
- `duration_seconds`: 5, 6, 7, or 8 seconds (Veo 3+ defaults to 8)
- `person_generation`: Safety setting - allow_adult (default), dont_allow, or allow_all
- `enhance_prompt`: Let the model enhance your prompt (default: true)
- `negative_prompt`: Elements to exclude from the video
- `seed`: Random seed for reproducibility (-1 for random)
- `output_directory`: Where to save the video (default: ComfyUI output folder)

**Outputs:**
- `video_path`: Path to the generated video file (.mp4)

**Features:**
- Veo 3 generates videos with synchronized audio
- Async generation with automatic polling (may take several minutes)
- Videos saved directly to disk
- Configurable aspect ratio and duration

**Example Prompts:**
- "A cat playing piano in a jazz club, cinematic lighting"
- "Drone footage of a futuristic city at sunset"
- "Time-lapse of flowers blooming in a garden"

---

#### Veo Image to Video
Generate videos from an input image and optional text prompt.

**Inputs:**
- `client`: Gemini API client (from Gemini API Config node)
- `image`: Input image (ComfyUI IMAGE tensor) - used as first frame or style reference
- `prompt`: Optional text description to guide the video generation
- `model`: veo-3.1-generate-preview (default, includes audio), veo-3.0-generate-001, or veo-2.0-generate-001
- `aspect_ratio`: 16:9 (landscape) or 9:16 (portrait)
- `duration_seconds`: 5, 6, 7, or 8 seconds (Veo 3+ defaults to 8)
- `person_generation`: Safety setting - allow_adult (default), dont_allow, or allow_all
- `enhance_prompt`: Let the model enhance your prompt (default: true)
- `negative_prompt`: Elements to exclude from the video
- `seed`: Random seed for reproducibility (-1 for random)
- `output_directory`: Where to save the video (default: ComfyUI output folder)

**Outputs:**
- `video_path`: Path to the generated video file (.mp4)

**Example Use Cases:**
- Animate a still photograph
- Create video from AI-generated images
- Turn product shots into video ads
- Animate artwork or illustrations

---

## Model Comparison

### Text Generation Models

| Model | Best For | Context Window | Notes |
|-------|----------|----------------|-------|
| **gemini-3-pro-preview** | Most intelligent, best reasoning | 1M tokens | Latest flagship model |
| **gemini-3-flash-preview** | Balanced speed and intelligence | 1M tokens | New balanced model |
| **gemini-2.5-pro** | Complex reasoning, thinking | 1M tokens | Stable, production-ready |
| **gemini-2.5-flash** | Best price-performance | 1M tokens | Recommended default |
| **gemini-2.5-flash-lite** | High-speed, cost-efficient | 1M tokens | Fastest, lowest cost |

### Image Generation Models

| Model | Best For | Notes |
|-------|----------|-------|
| **gemini-3-pro-image-preview** | Highest quality images | Best quality, character consistency |
| **gemini-2.5-flash-image** | Fast image generation | Fast, recommended for most uses |

**Note:** Image generation models output images instead of text.

### Video Generation Models (Veo)

| Model | Best For | Notes |
|-------|----------|-------|
| **veo-3.1-generate-preview** | Highest quality, latest features | Default, generates synchronized audio |
| **veo-3.1-fast-generate-preview** | Fast generation with audio | Faster variant of Veo 3.1 |
| **veo-3.0-generate-001** | Stable Veo 3 | Generates synchronized audio |
| **veo-3.0-fast-generate-001** | Fast Veo 3 | Faster variant of Veo 3 |
| **veo-2.0-generate-001** | Legacy video generation | No audio support |

**Pricing:** Veo 3+ is priced at $0.75 per second of video output.

**Note:** Video generation is asynchronous and may take several minutes. Videos are saved as .mp4 files.

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

### Text to Video
```
Gemini API Config → Veo Text to Video → [video_path output]
```

### Image to Video
```
Load Image → Gemini API Config → Veo Image to Video → [video_path output]
```

### Generate Image then Animate
```
Gemini API Config → Gemini Image Generation → Veo Image to Video → [video_path output]
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
- Preview models (like gemini-3-pro-preview) may have limited availability
- Try using gemini-2.5-flash or gemini-2.5-pro as stable alternatives

### Veo video generation timeout
- Video generation can take 2-10 minutes depending on duration and model
- The node polls every 20 seconds and times out after 40 minutes
- If you consistently get timeouts, try shorter durations or check your API quota

### Veo "person generation not approved" error
- Some Google Cloud projects need approval for generating videos with people
- Contact your Google account representative for approval
- Try setting `person_generation` to "dont_allow" as a workaround

### Cannot save video file
- Ensure the output directory exists and is writable
- Check disk space
- Try specifying a custom `output_directory` path

## Support

For issues, feature requests, or questions:
- Open an issue on GitHub
- Check the [Gemini API documentation](https://ai.google.dev/docs)

## License

See the main repository LICENSE file for details.
