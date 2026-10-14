# Gemini API Integration for ComfyUI

Complete Google Gemini API integration providing text generation, vision analysis, multi-turn conversations, image generation, image editing, **video generation (Veo)**, and safety controls for ComfyUI workflows.

**Version:** 2026.10.1
**Category in ComfyUI:** `ERPK/Gemini` and `ERPK/Gemini/Veo`
**SDK requirement:** `google-genai>=2.6.0` (per `gemini/requirements.txt`). Omni Flash needs it: 2.2.0 sends `response_format.aspect_ratio` as `aspectRatio`, which the API rejects

## Features

- **Text Generation** - Gemini 4 Argon, 3.1 Pro Preview, 3.8, 3.7, 3.6 and 3.5 Flash, and 3.5 Flash-Lite
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
   - Should see 13 nodes available (9 Gemini, 2 Veo, 2 Omni)

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
- `model`: gemini-3.8-flash (default), gemini-4-argon, gemini-3.1-pro-preview, gemini-3.7-flash (deprecated, served by 3.8 Flash), gemini-3.6-flash, gemini-3.5-flash (deprecated, served by 3.6 Flash), gemini-3.5-flash-lite
- `temperature`: 0.0-2.0 (creativity level, default: 0.7). Gemini 4 Argon ignores temperature, top_p and top_k
- `max_tokens`: 256-65536 (output length, default: 8192). Google recommends at least 32768 for Gemini 4 Argon
- `top_p`: 0.0-1.0 (nucleus sampling, default: 0.95, set 0.0 to disable)
- `top_k`: 0-100 (top-k sampling, default: 40, set 0 to disable)
- `stop_sequences`: Newline-separated sequences where generation stops (max 5)
- `response_mime_type`: Output format - "default", "text/plain", or "application/json"
- `response_schema`: JSON schema for structured output (used with application/json)
- `thinking_level`: Reasoning depth - "none" (default), "minimal", "low", "medium", "high". "none" sends no setting, so the model thinks at its own default level rather than turning thinking off. "minimal" is raised to "low" on 4 Argon, 3.1 Pro Preview, 3.7 Flash and 3.8 Flash, which reject it

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
- `model`: gemini-3.8-flash (default), gemini-4-argon, gemini-3.1-pro-preview, gemini-3.7-flash (deprecated, served by 3.8 Flash), gemini-3.6-flash, gemini-3.5-flash (deprecated, served by 3.6 Flash), gemini-3.5-flash-lite
- `chat_session`: Previous chat session (optional, connects from previous chat node)
- `reset_conversation`: Start new conversation (default: false)
- `temperature`: 0.0-2.0 (default: 0.7). Gemini 4 Argon ignores temperature, top_p and top_k
- `max_tokens`: 256-65536 (default: 8192). Google recommends at least 32768 for Gemini 4 Argon
- `top_p`: 0.0-1.0 (nucleus sampling, default: 0.95, set 0.0 to disable)
- `top_k`: 0-100 (top-k sampling, default: 40, set 0 to disable)
- `stop_sequences`: Newline-separated sequences where generation stops (max 5)
- `response_mime_type`: Output format - "default", "text/plain", or "application/json"
- `response_schema`: JSON schema for structured output (used with application/json)
- `thinking_level`: Reasoning depth - "none" (default), "minimal", "low", "medium", "high". "none" sends no setting, so the model thinks at its own default level rather than turning thinking off. "minimal" is raised to "low" on 4 Argon, 3.1 Pro Preview, 3.7 Flash and 3.8 Flash, which reject it

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
- `model`: gemini-3.8-flash (default), gemini-4-argon, gemini-3.1-pro-preview, gemini-3.7-flash (deprecated, served by 3.8 Flash), gemini-3.6-flash, gemini-3.5-flash (deprecated, served by 3.6 Flash), gemini-3.5-flash-lite
- `max_tokens`: 256-65536 (default: 8192). Google recommends at least 32768 for Gemini 4 Argon
- `temperature`: 0.0-2.0 (default: 0.4, lower for more factual). Gemini 4 Argon ignores temperature, top_p and top_k
- `top_p`: 0.0-1.0 (nucleus sampling, default: 0.95, set 0.0 to disable)
- `top_k`: 0-100 (top-k sampling, default: 40, set 0 to disable)
- `stop_sequences`: Newline-separated sequences where generation stops (max 5)
- `response_mime_type`: Output format - "default", "text/plain", or "application/json"
- `response_schema`: JSON schema for structured output (used with application/json)
- `thinking_level`: Reasoning depth - "none" (default), "minimal", "low", "medium", "high". "none" sends no setting, so the model thinks at its own default level rather than turning thinking off. "minimal" is raised to "low" on 4 Argon, 3.1 Pro Preview, 3.7 Flash and 3.8 Flash, which reject it

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
- `model`: gemini-nano-banana-2.1 (default, recommended), gemini-3.1-flash-image (deprecated in favour of Nano Banana 2.1, keeps the only 0.5K tier), gemini-3.1-flash-lite-image (Nano Banana 2 Lite, 1K only), or gemini-3-pro-image (professional)
- `temperature`: 0.0-2.0 (default: 1.0, higher for more creativity). The image models report a maximum of 1.0; higher values are accepted without error but have no documented effect
- `aspect_ratio`: Image dimensions - 14 ratios for Nano Banana 2.1 and 3.1 Flash (including 1:4, 4:1, 1:8, 8:1). 3.1 Flash Lite and 3 Pro have no 1:4, 4:1, 1:8 or 8:1 and use the closest supported ratio instead
- `image_size`: Resolution - "default", "0.5K", "1K", "2K", "4K". 3.1 Flash takes 0.5K-4K, Nano Banana 2.1 and 3 Pro 1K-4K, 3.1 Flash Lite 1K only; an unsupported size uses the model's smallest size
- `response_modalities`: "IMAGE" (image only) or "TEXT+IMAGE" (image + text description)
- `enable_google_search`: Enable Google Search grounding (Nano Banana 2.1, 3.1 Flash and 3 Pro; ignored on 3.1 Flash Lite, which does not support it)

**Outputs:**
- `image`: Generated image (ComfyUI IMAGE tensor)
- `description`: Text description (only when response_modalities is TEXT+IMAGE)

**Features:**
- Credentials resolved from ComfyUI Settings or config.ini
- Direct image output compatible with all ComfyUI image nodes
- Three image models: 3.1 Flash (best balance), 3.1 Flash Lite (fastest, cheapest), 3 Pro (professional quality)
- Configurable creativity with temperature
- Full aspect ratio support (up to 14 options)
- Resolution control from 0.5K to 4K
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
- `model`: gemini-nano-banana-2.1 (default, recommended), gemini-3.1-flash-image (deprecated in favour of Nano Banana 2.1, keeps the only 0.5K tier), gemini-3.1-flash-lite-image (Nano Banana 2 Lite, 1K only), or gemini-3-pro-image (professional)
- `temperature`: 0.0-2.0 (default: 1.0, higher for more creativity). The image models report a maximum of 1.0; higher values are accepted without error but have no documented effect
- `aspect_ratio`: Image dimensions - 14 ratios for Nano Banana 2.1 and 3.1 Flash (including 1:4, 4:1, 1:8, 8:1). 3.1 Flash Lite and 3 Pro have no 1:4, 4:1, 1:8 or 8:1 and use the closest supported ratio instead
- `image_size`: Resolution - "default", "0.5K", "1K", "2K", "4K". 3.1 Flash takes 0.5K-4K, Nano Banana 2.1 and 3 Pro 1K-4K, 3.1 Flash Lite 1K only; an unsupported size uses the model's smallest size
- `response_modalities`: "IMAGE" (image only) or "TEXT+IMAGE" (image + text description)
- `enable_google_search`: Enable Google Search grounding (Nano Banana 2.1, 3.1 Flash and 3 Pro; ignored on 3.1 Flash Lite, which does not support it)
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
- Resolution control from 0.5K to 4K
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

### Gemini Omni Video Generation

Generate 3-10 second video at 24 FPS, 360p to 4k, with Gemini Omni Flash 1.1 (`gemini-omni-1.1-flash`).

Unlike Veo, this model is reached through Google's Interactions API and returns the
video directly, so a generation completes in a single call with no polling.
That call gets at least a 15-minute timeout, because a 1080p or 4k render can outlast
the 5-minute default.

**Inputs:**
- `prompt`: What the video should show. Negative prompts are unsupported — state exclusions inline ("Do not show text on screen")
- `client`: Gemini API client (optional when the key is in ComfyUI Settings)
- `image`: Optional start image. Connecting one switches the model to image-to-video
- `aspect_ratio`: 16:9 (landscape) or 9:16 (portrait)
- `output_directory`: Where to save the video (default: ComfyUI output folder)
- `seed`: Cache control only — Omni Flash takes no API seed, so this is never sent. A fixed seed reuses the video you already paid for; -1 regenerates every queue
- `resolution`: 360p, 720p (default), 1080p or 4k. Google upscales 1080p and 4k; those come back as a Files API download because they exceed the 4MB inline limit. That delivery requires Google to store the interaction (`store=true`); the node deletes the downloaded file right after

**Outputs:**
- `video_path`: Path to the generated video file (.mp4)

**Not supported by this model:** system instructions, temperature, top_p, stop
sequences, negative prompts and audio-reference upload. This node does not expose
interpolation between first and last frames, and duration is chosen by the model
(3-10s). All output carries a SynthID watermark.

---

### Gemini Omni Reference to Video

Generate 3-10 second video that features the people, objects or style shown in reference
images (`reference_to_video` task).

**Inputs:**
- `prompt`: What the video should show. Cite references as `<IMAGE_REF_0>`, `<IMAGE_REF_1>`, ... in batch order
- `reference_images`: One or more reference images (use Batch Images to combine several)
- `client`, `aspect_ratio`, `resolution`, `output_directory`, `seed`: as on Gemini Omni Video Generation

**Outputs:**
- `video_path`: Path to the generated video file (.mp4)

---

**Omni tasks without a node:** Google does not offer `edit` or `extend` on uploaded videos in
the EEA, Switzerland or the UK, so no node wraps them. The API's task list also names `upscale`,
but `gemini-omni-1.1-flash` rejects it.

---

### Veo Video Generation Nodes

#### Veo Text to Video
Generate videos from text prompts using Google's Veo models.

**Inputs:**
- `client`: Gemini API client (from Gemini API Config node)
- `prompt`: Text description of the video to generate (max 2500 characters)
- `reference_images`: Up to 3 reference images (Veo 3.1 and 3.1 Fast only)
- `model`: veo-3.1-generate-preview (default, includes audio), veo-3.1-fast-generate-preview, or veo-3.1-lite-generate-preview
- `aspect_ratio`: 16:9 (landscape) or 9:16 (portrait)
- `resolution`: 720p (default), 1080p or 4k. Lite has no 4k. 1080p and 4k only support 8s
- `duration_seconds`: 4, 6 or 8 seconds (default 8). The 5 option only exists so older workflows load
- `person_generation`: allow_adult (default) or allow_all. dont_allow is rejected (Google's docs list allow_all for text-to-video, and allow_adult as the only value in EU/UK/CH/MENA)
- `seed`: Cache control only, never sent to the API. A fixed seed reuses the video already generated; -1 generates again on every queue
- `output_directory`: Where to save the video (default: ComfyUI output folder)

**Outputs:**
- `video_path`: Path to the generated video file (.mp4)

**Features:**
- Veo 3.1 generates videos with synchronized audio
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
- `image`: Input image (ComfyUI IMAGE tensor) - used as the first frame
- `last_frame_image`: Optional last frame for interpolation (requires 8s)
- `reference_images`: Up to 3 reference images (Veo 3.1 and 3.1 Fast only; requires 8s and 16:9; not with `last_frame_image`)
- `prompt`: Optional text description to guide the video generation
- `model`: veo-3.1-generate-preview (default, includes audio), veo-3.1-fast-generate-preview, or veo-3.1-lite-generate-preview
- `aspect_ratio`: 16:9 (landscape) or 9:16 (portrait)
- `resolution`: 720p (default), 1080p or 4k. Lite has no 4k. 1080p and 4k only support 8s
- `duration_seconds`: 4, 6 or 8 seconds (default 8). The 5 option only exists so older workflows load
- `person_generation`: allow_adult (default, and the only value Google's docs accept for image-to-video)
- `seed`: Cache control only, never sent to the API. A fixed seed reuses the video already generated; -1 generates again on every queue
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
| **gemini-4-argon** | Flagship reasoning | 1M tokens | $2/$10 per 1M through 2026-11-30, then $4/$20. Thinking low/medium/high (`minimal` is clamped to `low`). Ignores temperature, top_p and top_k. Each call gets at least a 15-minute timeout, as Google advises; set `max_tokens` to 32768 or more for hard prompts |
| **gemini-3.1-pro-preview** | Most advanced reasoning | 1M tokens | `minimal` thinking is clamped to `low` |
| **gemini-3.8-flash** | Latest Flash generation | 1M tokens | **Default**, same price as 3.6/3.7; `minimal` thinking is clamped to `low` |
| **gemini-3.7-flash** | Previous Flash generation | 1M tokens | Deprecated 2026-10-08: Google serves these requests with 3.8 Flash; `minimal` thinking is clamped to `low` |
| **gemini-3.6-flash** | Improved token efficiency | 1M tokens | Cheaper than 3.5 Flash |
| **gemini-3.5-flash** | Previous default | 1M tokens | Deprecated 2026-10-08: Google serves these requests with 3.6 Flash. Kept so saved workflows still load |

### Image Generation Models

| Model | Best For | Notes |
|-------|----------|-------|
| **gemini-nano-banana-2.1** | Latest flagship image model | **Default**, Nano Banana 2.1, 1K-4K, all 14 aspect ratios, Search grounding; about half the 3.1 Flash Image price at every size |
| **gemini-3.1-flash-image** | Previous flagship | Nano Banana 2, deprecated 2026-10-06 in favour of Nano Banana 2.1 (no shutdown date); the only model with a 0.5K tier |
| **gemini-3-pro-image** | Professional quality | Nano Banana Pro, best for character consistency (up to 14 reference images) |
| **gemini-3.1-flash-lite-image** | Fast, low-cost generation | Nano Banana 2 Lite, 1K only, no Google Search grounding |

**Note:** Image generation models output images instead of text. `gemini-3.1-flash-image` outputs 0.5K to 4K, `gemini-nano-banana-2.1` and `gemini-3-pro-image` 1K to 4K, and `gemini-3.1-flash-lite-image` 1K only (other requests are clamped).

### Video Generation Models (Veo)

| Model | Best For | Notes |
|-------|----------|-------|
| **veo-3.1-generate-preview** | Highest quality, latest features | Default, generates synchronized audio |
| **veo-3.1-fast-generate-preview** | Fast generation with audio | Faster variant of Veo 3.1 |
| **veo-3.1-lite-generate-preview** | Lightweight, lower cost | No reference-image support |

**Pricing** (per second of output, with audio): Veo 3.1 $0.40 (720p, 1080p) / $0.60 (4k); Veo 3.1 Fast $0.10 / $0.12 / $0.30; Veo 3.1 Lite $0.05 (720p) / $0.08 (1080p).

**Shutdown:** Google shuts down all three Veo 3.1 preview models on 2026-10-22; the listed replacement is Gemini Omni Flash.

**Note:** Video generation is asynchronous and may take several minutes. Videos are saved as .mp4 files.

### Veo client-side validators

Both Veo nodes run client-side validators before submitting the long-running job, to avoid eating a 4-5 minute generation just to see an opaque 400 from the API:

- **Duration normalization** — Veo 3.1 accepts `{4, 6, 8}`. Out-of-range values (including the legacy `5` option, kept so older workflows load) are snapped to the nearest valid duration with a warning.
- **Resolution gating** — Models that don't accept `4k` (Lite) are clamped to `1080p`. `1080p` and `4k` only support 8s, so a shorter duration is raised to 8s with a warning. `720p` is never upscaled.
- **person_generation** — Per Google's Veo docs, image-to-video accepts `allow_adult` only, and text-to-video accepts `allow_all`, or `allow_adult` in EU/UK/CH/MENA where that is the only allowed value. Anything else raises a `ValueError` before the API call.
- **i2v feature combos (Veo 3.1)** — `image + last_frame` interpolation requires `duration_seconds=8`; `reference_images` requires `duration_seconds=8` and `aspect_ratio=16:9`; `reference_images` cannot be combined with `image`/`last_frame`. Apart from the 8s rule for reference images, these gates are not in Google's parameter table but are confirmed by Google staff in forum threads — see `gemini/veo_nodes.py` for the linked discussions.

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
- Try gemini-3.8-flash (the default) as a stable alternative

### Veo video generation timeout
- Video generation can take 2-10 minutes depending on duration and model
- The node polls every 20 seconds and times out after 40 minutes
- If you consistently get timeouts, try shorter durations or check your API quota

### Veo "person generation not approved" error
- Some Google Cloud projects need approval for generating videos with people
- Contact your Google account representative for approval

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
