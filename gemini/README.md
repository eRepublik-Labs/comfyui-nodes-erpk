# Gemini API Integration for ComfyUI

Complete Google Gemini API integration providing text generation, vision analysis, multi-turn conversations, image generation, image editing, **video generation (Veo)**, and safety controls for ComfyUI workflows.

**Version:** 2026.7.2
**Category in ComfyUI:** `ERPK/Gemini` and `ERPK/Gemini/Veo`
**SDK requirement:** `google-genai>=2.2.0` (per `gemini/requirements.txt`)

## Features

- **Text Generation** - Use all Gemini models (3.1 Pro, 3 Pro, 3.5 Flash, 3 Flash, 2.5 Pro, 2.5 Flash)
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

4. **Configure API key** (choose one method, checked in priority order):

   **Method 1: ComfyUI Settings** (Recommended, highest priority)
   Go to **Settings > ERPK > API Keys** and enter your Google API key. You can also access this via right-click canvas > **ERPK Settings**.
   Keys configured here are stored in your user settings, not in workflows, so they won't leak when sharing.
   In multi-user installations, each user's keys are resolved separately.

   **Method 2: In ComfyUI Node**
   Enter API key directly in the Gemini API Config node (not recommended for shared workflows)

   **Method 3: config.ini File** (lowest priority)
   ```ini
   # Edit gemini/config.ini
   [gemini]
   # api_key = YOUR_GOOGLE_API_KEY_HERE
   ```

5. **Restart ComfyUI**

6. **Verify installation:**
   - Look for `ERPK/Gemini` and `ERPK/Gemini/Veo` categories in ComfyUI node menu
   - Should see 10 nodes available (8 Gemini + 2 Veo)

## Available Nodes

### Core Nodes

#### Gemini API Config
Initializes the Gemini API client. Optional if API key is configured via ComfyUI Settings or config.ini — Gemini nodes can run standalone.

**Inputs:**
- `api_key`: Optional API key (uses Settings/config if empty)

**Outputs:**
- `client`: Gemini API client instance

---

#### Gemini Text Generation
General-purpose text generation and completion.

**Inputs:**
- `client`: Gemini API client (optional)
- `prompt`: Text prompt
- `model`: gemini-3.5-flash (default), gemini-3.1-pro-preview, gemini-3-flash-preview, gemini-3.1-flash-lite, gemini-2.5-pro, gemini-2.5-flash, gemini-2.5-flash-lite
- `temperature`: 0.0-2.0 (creativity level, default: 0.7)
- `max_tokens`: 256-65536 (output length, default: 8192)
- `top_p`: 0.0-1.0 (nucleus sampling, default: 0.95, set 0.0 to disable)
- `top_k`: 0-100 (top-k sampling, default: 40, set 0 to disable)
- `stop_sequences`: Newline-separated sequences where generation stops (max 5)
- `response_mime_type`: Output format - "default", "text/plain", or "application/json"
- `response_schema`: JSON schema for structured output (used with application/json)
- `thinking_level`: Reasoning depth - "none" (default), "low", "medium", "high" (Gemini 3+ only)

**Outputs:**
- `response`: Generated text

**Example Uses:**
- Text completion and expansion
- Creative writing
- Content generation
- Text transformation
- **JSON mode**: Set response_mime_type to "application/json" for structured data extraction
- **Deep reasoning**: Set thinking_level to "high" for complex analytical tasks

---

#### Gemini Chat
Multi-turn conversation with message history preservation.

**Inputs:**
- `client`: Gemini API client (optional)
- `prompt`: Your message
- `model`: gemini-3.5-flash (default), gemini-3.1-pro-preview, gemini-3-flash-preview, gemini-3.1-flash-lite, gemini-2.5-pro, gemini-2.5-flash, gemini-2.5-flash-lite
- `chat_session`: Previous chat session (optional, connects from previous chat node)
- `reset_conversation`: Start new conversation (default: false)
- `temperature`: 0.0-2.0 (default: 0.7)
- `max_tokens`: 256-65536 (default: 8192)
- `top_p`: 0.0-1.0 (nucleus sampling, default: 0.95, set 0.0 to disable)
- `top_k`: 0-100 (top-k sampling, default: 40, set 0 to disable)
- `stop_sequences`: Newline-separated sequences where generation stops (max 5)
- `response_mime_type`: Output format - "default", "text/plain", or "application/json"
- `response_schema`: JSON schema for structured output (used with application/json)
- `thinking_level`: Reasoning depth - "none" (default), "low", "medium", "high" (Gemini 3+ only)

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
- `client`: Gemini API client (optional)
- `image`: ComfyUI image tensor (supports batches)
- `prompt`: Question or instruction about the image(s)
- `model`: gemini-3.5-flash (default), gemini-3.1-pro-preview, gemini-3-flash-preview, gemini-3.1-flash-lite, gemini-2.5-pro, gemini-2.5-flash, gemini-2.5-flash-lite
- `max_tokens`: 256-65536 (default: 8192)
- `temperature`: 0.0-2.0 (default: 0.4, lower for more factual)
- `top_p`: 0.0-1.0 (nucleus sampling, default: 0.95, set 0.0 to disable)
- `top_k`: 0-100 (top-k sampling, default: 40, set 0 to disable)
- `stop_sequences`: Newline-separated sequences where generation stops (max 5)
- `response_mime_type`: Output format - "default", "text/plain", or "application/json"
- `response_schema`: JSON schema for structured output (used with application/json)
- `thinking_level`: Reasoning depth - "none" (default), "low", "medium", "high" (Gemini 3+ only)

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
- `model`: gemini-3.1-flash-image (default, recommended), gemini-3-pro-image (professional), or gemini-2.5-flash-image (fast)
- `temperature`: 0.0-2.0 (default: 1.0, higher for more creativity)
- `aspect_ratio`: Image dimensions - 14 ratios for 3.1 Flash (including 1:4, 4:1, 1:8, 8:1), 10 ratios for others
- `image_size`: Resolution - "default", "1K", "2K", "4K" (1K-4K for 3.1 Flash and 3 Pro; 2.5 Flash fixed at 1024px)
- `response_modalities`: "IMAGE" (image only) or "TEXT+IMAGE" (image + text description)
- `enable_google_search`: Enable Google Search grounding (Gemini 3 models only)

**Outputs:**
- `image`: Generated image (ComfyUI IMAGE tensor)
- `description`: Text description (only when response_modalities is TEXT+IMAGE)

**Features:**
- Credentials resolved from ComfyUI Settings or config.ini
- Direct image output compatible with all ComfyUI image nodes
- Three image models: 3.1 Flash (best balance), 3 Pro (professional quality), 2.5 Flash (speed)
- Configurable creativity with temperature
- Full aspect ratio support (up to 14 options)
- Resolution control from 1K to 4K
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
- `image`: Input image(s) to edit (up to 14 reference images). Use ComfyUI's **Batch Images** node to combine multiple images.
- `prompt`: Text description of how to modify the image(s)
- `client`: Optional Gemini API client (from Gemini API Config node)
- `model`: gemini-3.1-flash-image (default, recommended), gemini-3-pro-image (professional), or gemini-2.5-flash-image (fast)
- `temperature`: 0.0-2.0 (default: 1.0, higher for more creativity)
- `aspect_ratio`: Image dimensions - 14 ratios for 3.1 Flash (including 1:4, 4:1, 1:8, 8:1), 10 ratios for others
- `image_size`: Resolution - "default", "1K", "2K", "4K" (1K-4K for 3.1 Flash and 3 Pro; 2.5 Flash fixed at 1024px)
- `response_modalities`: "IMAGE" (image only) or "TEXT+IMAGE" (image + text description)
- `enable_google_search`: Enable Google Search grounding (Gemini 3 models only)
- `additional_images`: Optional additional reference images (combined with primary image input, up to 14 total)

**Outputs:**
- `image`: Edited image (ComfyUI IMAGE tensor)
- `description`: Text description (only when response_modalities is TEXT+IMAGE)

**Features:**
- Credentials resolved from ComfyUI Settings or config.ini
- Gemini 3 models support up to 14 reference images (up to 6 objects, up to 5 humans)
- Image-to-image editing with natural language instructions
- Compatible with all ComfyUI image nodes
- Full aspect ratio support (up to 14 options)
- Resolution control from 1K to 4K
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

**Referencing Images in Prompts:**
Gemini understands images by position and content. You can reference them as:
- **By order:** "the first image", "the second image", "image 1", "image 2"
- **By content:** "the person wearing red", "the logo", "the background"
- **By role:** "the style reference", "the subject", "the product"

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
- `model`: veo-3.1-generate-preview (default, includes audio), veo-3.1-fast-generate-preview, or veo-3.1-lite-generate-preview
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
- `model`: veo-3.1-generate-preview (default, includes audio), veo-3.1-fast-generate-preview, or veo-3.1-lite-generate-preview
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
| **gemini-3.1-pro-preview** | Most advanced reasoning | 1M tokens | Supports thinking levels |
| **gemini-3.5-flash** | Frontier intelligence at high speed and low cost | 1M tokens | **Default**, stable, built for multi-step and long-horizon tasks |
| **gemini-3-flash-preview** | Balanced speed and intelligence | 1M tokens | Balanced model |
| **gemini-3.1-flash-lite** | High-volume, low-latency tasks | 1M tokens | Fastest, most cost-efficient |
| **gemini-2.5-pro** | Complex reasoning, thinking | 1M tokens | Stable, production-ready |
| **gemini-2.5-flash** | Best price-performance | 1M tokens | Stable, production-ready |
| **gemini-2.5-flash-lite** | High-speed, cost-efficient | 1M tokens | Fastest, lowest cost |

### Image Generation Models

| Model | Best For | Notes |
|-------|----------|-------|
| **gemini-3.1-flash-image** | Latest flagship image model | **Default**, Nano Banana 2, 4K output + Image Search Grounding |
| **gemini-3-pro-image** | Professional quality | Nano Banana Pro, best for character consistency (up to 14 reference images) |
| **gemini-2.5-flash-image** | Fast image generation | Stable, lowest latency |

**Note:** Image generation models output images instead of text. Resolution for `gemini-3.1-flash-image` and `gemini-3-pro-image` ranges from 1K to 4K; `gemini-2.5-flash-image` is fixed at 1024px.

### Video Generation Models (Veo)

| Model | Best For | Notes |
|-------|----------|-------|
| **veo-3.1-generate-preview** | Highest quality, latest features | Default, generates synchronized audio |
| **veo-3.1-fast-generate-preview** | Fast generation with audio | Faster variant of Veo 3.1 |
| **veo-3.1-lite-generate-preview** | Lightweight, lower cost | No reference-image support |

**Pricing:** Veo 3+ is priced at $0.75 per second of video output.

**Note:** Video generation is asynchronous and may take several minutes. Videos are saved as .mp4 files.

### Veo client-side validators

Both Veo nodes run client-side validators before submitting the long-running job, to avoid eating a 4-5 minute generation just to see an opaque 400 from the API:

- **Duration normalization** — Veo 3.x accepts `{4, 6, 8}`. Out-of-range values are snapped to the nearest valid duration with a warning.
- **Resolution gating** — Models that don't accept `4k` (Lite) are clamped to `1080p`. On Veo 3.x, an 8s duration with `720p` and no reference images is auto-bumped to `1080p`.
- **person_generation** — Veo 3.x image-to-video rejects `allow_all` server-side; the validator raises a `ValueError` early. Text-to-video paths accept the full enum.
- **i2v feature combos (Veo 3.1)** — `image + last_frame` interpolation requires `duration_seconds=8`; `reference_images` requires `duration_seconds=8` and `aspect_ratio=16:9`; `reference_images` cannot be combined with `image`/`last_frame`. These gates are not documented in Google's parameter table but are confirmed by Google staff in forum threads — see `gemini/veo_nodes.py` for the linked discussions.

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
- Set your API key via ComfyUI Settings (**Settings > ERPK > API Keys**, recommended)
- Or verify your API key is set via the node input or config.ini
- Check that the config.ini file has the correct format

### "Response blocked by safety filters" error
- Your prompt or the model's response triggered safety filters
- Try using the Gemini Safety Settings node to adjust thresholds
- Rephrase your prompt to be less ambiguous

### Import errors
- Ensure you've installed dependencies: `pip install -r requirements.txt`
- Check that you're using Python 3.10 or higher
- Restart ComfyUI after installing dependencies

### Model not available
- Preview models (like gemini-3.1-pro-preview) may have limited availability
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
