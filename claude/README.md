# Claude API Integration for ComfyUI

Complete Claude API integration providing text generation, prompt enhancement, vision analysis, and conversational AI capabilities for ComfyUI workflows.

**Version:** 2026.10.1
**Category in ComfyUI:** `ERPK/Claude`

## Features

- **Prompt Enhancement** - Transform simple prompts into detailed descriptions with 51 artistic styles
- **Vision Analysis** - Analyze images with Claude's multimodal capabilities (up to 20 images)
- **Text Generation** - General-purpose text completion and generation
- **Conversations** - Multi-turn dialogues with context preservation
- **Token Management** - Count tokens, estimate costs, automatic context trimming
- **Structured Output** - Schema-constrained JSON via structured outputs
- **Cost Optimization** - Prompt caching, effort control, per-model cost tracking
- **Full ComfyUI Integration** - Native node types, workflow compatibility

## Installation

### Prerequisites

- ComfyUI installed and running
- Python 3.10 or higher
- `anthropic>=1.11.0` (installed by `claude/requirements.txt`; an existing install on an older SDK must upgrade with `pip install -U -r claude/requirements.txt`)
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

   When multiple methods are configured, they are checked in priority order: Settings > Node widget > config.ini.

   **Method 1: ComfyUI Settings** (Recommended, highest priority)
   Go to **Settings > ERPK > API Keys** (or right-click canvas > **ERPK Settings**) and enter your Anthropic API key.
   Keys configured here are stored in your user settings, not in workflows, so they won't leak when sharing.
   In multi-user installations, each user's keys are resolved separately.

   **Method 2: In ComfyUI Node**
   Enter API key directly in the Claude API Client node (not recommended for shared workflows)

   **Method 3: config.ini File** (lowest priority)
   ```ini
   # Edit claude/config.ini
   [claude]
   # api_key = YOUR_API_KEY_HERE
   ```

5. **Restart ComfyUI**

6. **Verify installation:**
   - Look for `ERPK/Claude` category in ComfyUI node menu
   - Should see 10 nodes available

## Available Nodes

### Core Nodes

#### Claude API Client
Initializes the Claude API client. Optional if API key is configured in ComfyUI Settings — generation nodes can run standalone.

**Inputs:**
- `model`: claude-sonnet-5-5 (default), claude-sonnet-5, claude-opus-5-5, claude-opus-5, claude-fable-5-1, claude-fable-5
- `api_key`: Optional API key (uses Settings/config if empty)
- `enable_streaming`: Enable streaming responses
- `enable_caching`: Send automatic prompt caching (see [Prompt Caching](#prompt-caching))

**Outputs:**
- `client`: Claude API client instance

#### Claude Prompt Enhancer
**PRIMARY FEATURE** - Transforms simple prompts into detailed, styled descriptions.

**Inputs:**
- `client`: Claude API client (optional)
- `prompt`: Simple prompt (e.g., "a cat")
- `style`: 51 styles (photorealistic, cinematic, fantasy, cyberpunk, anime, etc.)
- `detail_level`: minimal, moderate, detailed, ultra-detailed
- `temperature`: Ignored. Current Claude models reject it, so it is never sent; kept so saved workflows load
- `max_tokens`: 256-128000 (output length; thinking counts toward it)
- `use_streaming`: Enable streaming
- `model`: Model override for this call, or inherit the client's model (default)
- `effort`: (model default), low, medium, high, xhigh, max. (model default) leaves the model's own default

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
- `max_tokens`: 256-128000 (output length; thinking counts toward it)
- `model`: Model override for this call, or inherit the client's model (default)
- `effort`: (model default), low, medium, high, xhigh, max. (model default) leaves the model's own default

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
- `temperature`: Ignored. Current Claude models reject it, so it is never sent; kept so saved workflows load
- `max_tokens`: 256-128000 (output length; thinking counts toward it)
- `use_streaming`: Enable streaming
- `model`: Model override for this call, or inherit the client's model (default)
- `effort`: (model default), low, medium, high, xhigh, max. (model default) leaves the model's own default

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
- `auto_trim`: Auto-trim old messages to fit the context window of the model this node calls
- `reset_conversation`: Start fresh conversation
- `temperature`: Ignored. Current Claude models reject it, so it is never sent; kept so saved workflows load
- `max_tokens`: 256-128000 (output length; thinking counts toward it)
- `model`: Model override for this call, or inherit the client's model (default)
- `effort`: (model default), low, medium, high, xhigh, max. (model default) leaves the model's own default

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
- `stats`: Formatted usage statistics. Each response is priced by the model that answered it (input, output, cache reads, 5-minute cache writes); a model missing from `pricing.json` is listed as not costed

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
Gets JSON from Claude that matches your tool's schema. Uses Anthropic's structured outputs (`output_config.format` with the tool's `input_schema` as a JSON Schema), which constrains the reply to the schema. Earlier versions forced tool use, which Sonnet 5.5, Opus 5.5 and Fable 5.1 reject.

**Inputs:**
- `client`: Claude API client (optional)
- `prompt`: What to extract or generate
- `tool`: Tool definition (exactly 1 tool from Tool Definition node)
- `system_prompt`: Optional system prompt
- `temperature`: Ignored. Current Claude models reject it, so it is never sent; kept so saved workflows load
- `max_tokens`: 256-128000 (default 4096; thinking counts toward it)
- `effort`: (model default), low, medium, high, xhigh, max. (model default) leaves the model's own default

**Outputs:**
- `json_output`: The JSON reply (pretty-printed)
- `thinking`: Claude's summarized thinking for this reply; empty when it answered without thinking

**Notes:**
- The `tool` input must contain exactly 1 tool — connecting a chain of multiple tools will raise an error
- The tool's name and description are added to the system prompt so Claude knows what the JSON is for
- Structured outputs require `"additionalProperties": false` on every object. The node adds it where the schema leaves it out and rejects a schema that sets it to anything else
- A reply cut off at `max_tokens` raises an error rather than returning partial JSON
- Empty or whitespace-only prompts are rejected at queue time

**Use Cases:**
- Extract structured data from unstructured text
- Generate structured content (e.g. metadata, tags, classifications)
- Parse and normalize data into a consistent schema
- Schema-matching JSON without regex parsing

## Prompt Enhancement Styles

The Claude Prompt Enhancer supports 51 artistic styles:

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
Enabled by default (`enable_caching` on Claude API Client). Each request carries a top-level `cache_control: {"type": "ephemeral"}`, Anthropic's automatic caching: the API caches the longest reusable prompt prefix (system prompt, then messages).

**How it works:**
- The first request writes the prefix to a 5-minute cache, billed at 1.25x the input price
- A repeat within 5 minutes reads it at the cache-read price: 0.1x input on most models, 0.05x on Opus 5.5, 0.025x on Fable 5.1
- Prompts below the model's minimum cacheable length are not cached
- Measured 2026-10-01 on Sonnet 5.5: a 7,226-token system prompt sent twice wrote 7,226 cache tokens on the first call and read 7,226 on the second

**Pricing (Claude Sonnet 5.5, per million tokens):**
- Input: $2
- Output: $10
- 5-minute cache write: $2.50
- Cache read: $0.20

### Effort
Text Generation, Conversation, Prompt Enhancer, Vision Analysis and Structured Output have an `effort` widget (low, medium, high, xhigh, max). Lower effort spends fewer thinking and output tokens. `(model default)` sends nothing, so each model keeps its own default (high; medium on Opus 5.5)

### Token Management
- Use Token Counter node to check prompt lengths before generation
- Enable auto-trim in Conversation nodes to stay within context window
- Monitor usage with Usage Stats node

### Model Selection
Every offered model has a 1M-token context window, up to 128K output tokens, adaptive thinking, and rejects temperature/top_p/top_k (the client never sends them).
- **Claude Sonnet 5.5** (default): $2/1M in, $10/1M out - Newest Sonnet, the general-purpose choice
- **Claude Sonnet 5**: $2/1M in, $10/1M out - Previous Sonnet
- **Claude Opus 5.5**: $4/1M in, $20/1M out - Highest-capability Opus; cache reads at 0.05x
- **Claude Opus 5**: $5/1M in, $25/1M out - Previous Opus
- **Claude Fable 5.1**: $10/1M in, $50/1M out - Most capable model; needs an organization with data retention enabled
- **Claude Fable 5**: $10/1M in, $50/1M out - Previous Fable; same access requirement

Removed 2026-10-01: claude-opus-4-8, claude-opus-4-7, claude-sonnet-4-6, claude-opus-4-6, claude-haiku-4-5-20251001, claude-sonnet-4-5-20250929. A saved workflow that selects one fails validation until you pick a current model.

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
**Solution:** Set API key via ComfyUI Settings (recommended), config.ini, or node input.
Go to **Settings > ERPK > API Keys** (or right-click canvas > **ERPK Settings**).

### "Rate limit hit" Errors
**Solution:** Reduce request frequency. Client auto-retries with exponential backoff.

### Nodes not appearing in ComfyUI
**Solution:**
1. Check `ComfyUI/custom_nodes/ERPK/claude/__init__.py` exists
2. Restart ComfyUI completely
3. Check terminal for error messages
4. Verify dependencies installed: `pip list | grep anthropic`

### "data retention enabled" (400) or "model: claude-fable-5" (404)
**Cause:** Fable models are only available to organizations with data retention enabled.
**Solution:** Pick another model, or enable data retention for your organization in the Anthropic Console.

### "unexpected keyword argument" TypeError
**Cause:** The installed `anthropic` SDK is older than 1.11.0.
**Solution:** `pip install -U -r claude/requirements.txt` in ComfyUI's Python environment, then restart ComfyUI.

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
- Every offered model: 1,000,000 tokens
- Auto-trimming in Conversation reserves `max_tokens` + 1,000 tokens for the response and always keeps the 4 most recent messages
- Oldest messages removed first when trimming

### Caching Behavior
- Automatic caching via top-level `cache_control` when `enable_caching` is on
- Cache duration: 5 minutes, refreshed on each hit
- Cache reads and writes tracked and costed in Usage Stats

## API Reference

**Anthropic Documentation:** https://docs.anthropic.com/
**Claude Models:** https://docs.anthropic.com/claude/docs/models-overview
**Pricing:** https://anthropic.com/pricing
**API Keys:** https://console.anthropic.com/settings/keys

## License

MIT License

## Support

For issues, questions, or contributions, please visit the repository or contact the maintainers.

**Version:** 2026.10.1
**Last Updated:** May 2026
