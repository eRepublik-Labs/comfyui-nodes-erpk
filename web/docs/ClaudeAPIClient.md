<!-- ABOUTME: Help documentation for the Claude API Client ComfyUI node. -->
<!-- ABOUTME: Initializes a Claude API client with model selection and settings. -->

# Claude API Client

Initializes a Claude API client for use by other nodes. Optional if your API key is configured in ComfyUI Settings — generation nodes can create their own client automatically.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| model | Combo | claude-sonnet-5-5 | Claude model to use. Options: claude-sonnet-5-5, claude-sonnet-5, claude-opus-5-5, claude-opus-5, claude-fable-5-1, claude-fable-5 |
| api_key | String | (empty) | Anthropic API key (optional). If empty, uses Settings or config.ini |
| enable_streaming | Boolean | False | Enable streaming responses (optional). ComfyUI may not display streaming in real-time |
| enable_caching | Boolean | True | Send automatic prompt caching (optional). The first call writes the prompt prefix at 1.25x the input price; repeats within 5 minutes read it at the cache-read price (0.1x input on most models). Prompts below the model's minimum cacheable length are not cached |

## Output

| Output | Type | Description |
|--------|------|-------------|
| client | CLAUDE_API_CLIENT | Configured Claude API client instance |

## Notes

- API key resolution order: ComfyUI Settings > node widget > config.ini
- Sonnet 5.5 is the default general-purpose model; Opus 5.5 is the highest-capability tier
- Every offered model uses adaptive thinking and rejects temperature/top_p/top_k, so the client never sends them
- Fable 5 and Fable 5.1 need an organization with data retention enabled; other organizations get a 404 or a "data retention" 400
- Prompt caching is enabled by default; Usage Stats shows the cache reads and writes it produced
- Requires anthropic>=1.11.0
