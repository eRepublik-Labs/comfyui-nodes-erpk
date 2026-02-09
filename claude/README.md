# Claude API Integration for ComfyUI

Complete Claude API integration providing text generation, prompt enhancement, vision analysis, and conversational AI capabilities for ComfyUI workflows.

**Version:** 2026.2.3
**Category in ComfyUI:** `ERPK/Claude`

## Features

- **Prompt Enhancement** - Transform simple prompts into detailed descriptions with 50+ artistic styles
- **Vision Analysis** - Analyze images with Claude's multimodal capabilities (up to 20 images)
- **Text Generation** - General-purpose text completion and generation
- **Conversations** - Multi-turn dialogues with context preservation
- **Token Management** - Count tokens, estimate costs, automatic context trimming
- **Structured Output** - Guaranteed JSON output via forced tool use
- **Cost Optimization** - Prompt caching (up to 90% savings), streaming support
- **Full ComfyUI Integration** - Native node types, workflow compatibility

## Installation

### Prerequisites

- ComfyUI installed and running
- Python 3.8 or higher
- Anthropic API key ([get one here](https://console.anthropic.com/settings/keys))

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
   pip install -r claude/requirements.txt
   ```

4. **Configure API key** (choose one method):

   When multiple methods are configured, they are checked in priority order: Settings > Node widget > Environment variable > config.ini.

   **Method 1: ComfyUI Settings** (Recommended, highest priority)
   Go to **Settings > ERPK > API Keys** (or right-click canvas > **ERPK Settings**) and enter your Anthropic API key.
   Keys configured here are stored in your user settings, not in workflows, so they won't leak when sharing.

   **Method 2: Environment Variable**
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

   **Method 3: config.ini File** (lowest priority)
   ```ini
   # Edit claude/config.ini
   [claude]
   # api_key = YOUR_API_KEY_HERE
   ```

   **Method 4: In ComfyUI Node**
   Enter API key directly in the Claude API Client node (not recommended for shared workflows)

5. **Restart ComfyUI**

6. **Verify installation:**
   - Look for `ERPK/Claude` category in ComfyUI node menu
   - Should see 10 nodes available

## Available Nodes

### Core Nodes

#### Claude API Client
Initializes the Claude API client. Optional if API key is configured in ComfyUI Settings — generation nodes can run standalone.

**Inputs:**
- `model`: claude-sonnet-4-5 (default), claude-opus-4-6, claude-haiku-4-5
- `api_key`: Optional API key (uses env/config if empty)
- `enable_streaming`: Enable streaming responses
- `enable_caching`: Enable prompt caching for cost savings

**Outputs:**
- `client`: Claude API client instance

#### Claude Prompt Enhancer
**PRIMARY FEATURE** - Transforms simple prompts into detailed, styled descriptions.

**Inputs:**
- `client`: Claude API client (optional)
- `prompt`: Simple prompt (e.g., "a cat")
- `style`: 50+ styles (photorealistic, cinematic, fantasy, cyberpunk, anime, etc.)
- `detail_level`: minimal, moderate, detailed, ultra-detailed
- `temperature`: 0.0-1.0 (creativity level)
- `max_tokens`: 256-4096 (output length)
- `use_streaming`: Enable streaming

**Outputs:**
- `enhanced_prompt`: Detailed, styled prompt

**Example:**
- Input: "a cat"
- Style: photorealistic
- Output: "A majestic orange tabby cat with piercing emerald eyes, sitting regally on a plush velvet cushion. Soft, diffused studio lighting creates gentle shadows highlighting the cat's luxurious fur texture. Shot with 85mm lens at f/2.8 for shallow depth of field, with bokeh background. Professional pet photography, 8K resolution, photorealistic rendering..."

### Vision Nodes

#### Claude Vision Analysis
Analyzes images using Claude's multimodal capabilities.

**Inputs:**
- `client`: Claude API client (optional)
- `image`: IMAGE tensor (ComfyUI format)
- `question`: Question or instruction about the image
- `additional_images`: Optional (up to 19 more images)
- `detail_level`: low, medium, high
- `max_tokens`: Output length

**Outputs:**
- `analysis`: Detailed image analysis text

**Use Cases:**
- Generate image captions for training data
- Reverse-engineer prompts from images
- Quality assessment and feedback
- Extract structured information from images

### Text Generation Nodes

#### Claude Text Generation
General-purpose text generation.

**Inputs:**
- `client`: Claude API client (optional)
- `prompt`: User prompt
- `system_prompt`: Optional system prompt
- `temperature`: Creativity level
- `max_tokens`: Output length
- `use_streaming`: Enable streaming

**Outputs:**
- `response`: Generated text

### Conversation Nodes

#### Claude Conversation
Multi-turn conversations with message history.

**Inputs:**
- `client`: Claude API client (optional)
- `prompt`: Your message
- `conversation_history`: Previous conversation state (connect from previous node)
- `system_prompt`: Optional (only for new conversations)
- `auto_trim`: Auto-trim old messages to fit context window
- `reset_conversation`: Start fresh conversation
- `temperature`, `max_tokens`: Generation parameters

**Outputs:**
- `response`: Claude's response
- `conversation_history`: Updated conversation state (connect to next conversation node)

#### Claude Conversation Info
Display conversation statistics and token usage.

**Inputs:**
- `conversation_history`: Conversation state to inspect

**Outputs:**
- `info`: Formatted statistics (message counts, token usage, context %)

### Utility Nodes

#### Claude Token Counter
Count tokens and estimate API costs.

**Inputs:**
- `text`: Text to analyze
- `model`: Model for pricing
- `client`: Optional (for accurate counting)

**Outputs:**
- `token_count`: Number of tokens
- `summary`: Formatted analysis with cost estimates

#### Claude Usage Stats
Display cumulative token usage and costs for a client.

**Inputs:**
- `client`: Claude API client
- `reset_stats`: Reset stats after displaying

**Outputs:**
- `stats`: Formatted usage statistics

### Tool Use Nodes

**Category in ComfyUI:** `ERPK/Claude/Tools`

#### Claude Tool Definition
Builds an Anthropic tool definition for use with structured output. Chainable — connect multiple Tool Definition nodes to build a tool list.

**Inputs:**
- `tool_name`: snake_case identifier (e.g. `extract_person`)
- `description`: What the tool does (shown to the model)
- `parameters_json`: JSON Schema for the tool's input parameters
- `previous_tools`: Optional chain from another Tool Definition node

**Outputs:**
- `tools`: Tool definition list (`CLAUDE_TOOLS`)

**Notes:**
- If a chained tool has the same name as a previous one, it replaces the earlier definition
- Invalid JSON in `parameters_json` raises an error at queue time

**Example parameters_json:**
```json
{
  "type": "object",
  "properties": {
    "name": {"type": "string", "description": "Person's full name"},
    "age": {"type": "integer", "description": "Person's age"}
  },
  "required": ["name"]
}
```

#### Claude Structured Output
Forces Claude to respond with structured JSON matching your tool schema. Uses Anthropic's forced tool use — the model is guaranteed to produce valid JSON conforming to your schema.

**Inputs:**
- `client`: Claude API client (optional)
- `prompt`: What to extract or generate
- `tool`: Tool definition (exactly 1 tool from Tool Definition node)
- `system_prompt`: Optional system prompt
- `temperature`: 0.0-1.0 (default 0.0 — low for consistency)
- `max_tokens`: 256-8192 (default 4096)

**Outputs:**
- `json_output`: Extracted JSON string (pretty-printed)
- `thinking`: Any text blocks Claude produced before the tool use block. Usually empty at low temperature. This captures optional reasoning text from the response, not Anthropic's extended thinking feature (which is a separate API capability).

**Notes:**
- The `tool` input must contain exactly 1 tool — connecting a chain of multiple tools will raise an error
- Empty or whitespace-only prompts are rejected at queue time

**Use Cases:**
- Extract structured data from unstructured text
- Generate structured content (e.g. metadata, tags, classifications)
- Parse and normalize data into a consistent schema
- Guaranteed JSON output without regex parsing

## Prompt Enhancement Styles

The Claude Prompt Enhancer supports 50+ artistic styles:

**Photography:**
- photorealistic, cinematic, portrait, landscape, street_photography, macro_photography, fashion_photography, architectural

**Digital Art:**
- digital_art, concept_art, low_poly, voxel_art, isometric, pixel_art, glitch_art

**Traditional Art:**
- oil_painting, watercolor, impressionist, expressionist, abstract, minimalist, maximalist

**Historical Periods:**
- baroque, renaissance, rococo, romantic, realism, art_nouveau, art_deco, pop_art

**Fantasy & Sci-Fi:**
- fantasy_art, medieval_fantasy, dark_fantasy, sci_fi, cyberpunk, steampunk, solarpunk, dieselpunk, biopunk, atompunk, retro_futurism

**Anime & Manga:**
- anime, kawaii

**Dark & Atmospheric:**
- gothic, noir, horror, cosmic_horror, surreal

**And more!**

Each style has custom system prompts that guide Claude to generate appropriate descriptions with style-specific elements, lighting, composition, and technical details.

## Cost Optimization

### Prompt Caching
Enabled by default. Caches system prompts to reduce costs by up to 90% for repeated requests.

**How it works:**
- System prompts are marked for caching
- Subsequent requests with same system prompt read from cache
- Cache read tokens cost 0.1x of regular input tokens

**Pricing (Claude Sonnet 4.5):**
- Input: $3 / million tokens
- Output: $15 / million tokens
- Cache Read: $0.30 / million tokens (90% savings)

### Token Management
- Use Token Counter node to check prompt lengths before generation
- Enable auto-trim in Conversation nodes to stay within context window
- Monitor usage with Usage Stats node

### Model Selection
- **Claude Haiku 4.5**: $1/1M in, $5/1M out - Fastest, cheapest for simple tasks
- **Claude Sonnet 4.5**: $3/1M in, $15/1M out - Best balance (default)
- **Claude Opus 4.6**: $5/1M in, $25/1M out - Most intelligent, best for agents and coding

## Workflow Examples

### Basic Prompt Enhancement
```
[Claude API Client] → [Claude Prompt Enhancer] → [Your Image Generation Node]
```

### Image Analysis Feedback Loop
```
[Generate Image] → [Claude Vision Analysis] → [Claude Prompt Enhancer] → [Regenerate]
```

### Multi-Turn Conversation
```
[Claude API Client] → [Claude Conversation] → [Claude Conversation] → [Claude Conversation]
                             ↑_____________↓           ↑_____________↓
                           (conversation_history connections)
```

### Structured Data Extraction
```
[Claude API Client] → [Claude Tool Definition] → [Claude Structured Output] → [Use JSON]
```

### Cost-Aware Generation
```
[Claude Token Counter] → [Decide if OK] → [Claude Text Generation]
```

## Troubleshooting

### "No API key found" Error
**Solution:** Set API key via ComfyUI Settings (recommended), environment variable, config.ini, or node input.
Go to **Settings > ERPK > API Keys** (or right-click canvas > **ERPK Settings**) or:
```bash
export ANTHROPIC_API_KEY="your-key"
```

### "Rate limit hit" Errors
**Solution:** Reduce request frequency. Client auto-retries with exponential backoff.

### Nodes not appearing in ComfyUI
**Solution:**
1. Check `ComfyUI/custom_nodes/ERPK/claude/__init__.py` exists
2. Restart ComfyUI completely
3. Check terminal for error messages
4. Verify dependencies installed: `pip list | grep anthropic`

### "Context window exceeded" Error
**Solution:**
- Enable `auto_trim` in Conversation nodes
- Use Token Counter to check prompt lengths
- Reduce `max_tokens` parameter
- Start new conversation with `reset_conversation`

### Streaming not working in ComfyUI
**Note:** ComfyUI may not display streaming in real-time. Responses are collected and returned when complete. Set `use_streaming=False` for consistent behavior.

### Image validation errors
**Solution:**
- Max image size: 5MB
- Max dimensions: 8000x8000px
- Supported formats: JPEG, PNG, GIF, WebP
- Node auto-resizes oversized images

## Technical Details

### Architecture
- **Client Layer**: `claude_api/client.py` - API communication, retry logic, token tracking
- **Utilities**: `claude_api/utils.py` - Token management, image conversion, validation
- **Nodes**: Individual `.py` files for each node type
- **Registration**: `__init__.py` - ComfyUI node registration

### Custom ComfyUI Types
- `CLAUDE_API_CLIENT`: Client instance (passed between nodes)
- `CLAUDE_CONVERSATION`: Conversation state (message history + system prompt)
- `CLAUDE_TOOLS`: List of Anthropic tool definitions (for structured output)

### Context Window
- All models: 200,000 tokens
- Auto-trimming reserves 20,000 tokens for responses
- Oldest messages removed first when trimming

### Caching Behavior
- System prompts cached automatically
- Cache duration: Ephemeral (session-based)
- Cache hits tracked in Usage Stats

## API Reference

**Anthropic Documentation:** https://docs.anthropic.com/
**Claude Models:** https://docs.anthropic.com/claude/docs/models-overview
**Pricing:** https://anthropic.com/pricing
**API Keys:** https://console.anthropic.com/settings/keys

## License

MIT License

## Support

For issues, questions, or contributions, please visit the repository or contact the maintainers.

**Version:** 2026.2.3
**Last Updated:** February 2026
