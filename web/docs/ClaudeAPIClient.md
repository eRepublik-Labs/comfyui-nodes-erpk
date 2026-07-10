<!-- ABOUTME: Help documentation for the Claude API Client ComfyUI node. -->
<!-- ABOUTME: Initializes a Claude API client with model selection and settings. -->

# Claude API Client

Initializes a Claude API client for use by other nodes. Optional if your API key is configured in ComfyUI Settings — generation nodes can create their own client automatically.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| model | Combo | claude-sonnet-5 | Claude model to use. Options: claude-sonnet-5, claude-opus-4-8, claude-fable-5, claude-opus-4-7, claude-sonnet-4-6, claude-opus-4-6, claude-haiku-4-5-20251001, claude-sonnet-4-5-20250929 |
| api_key | String | (empty) | Anthropic API key (optional). If empty, uses Settings or config.ini |
| enable_streaming | Boolean | False | Enable streaming responses (optional). ComfyUI may not display streaming in real-time |
| enable_caching | Boolean | True | Enable prompt caching for cost optimization (optional). Up to 90% savings on repeated prompts |

## Output

| Output | Type | Description |
|--------|------|-------------|
| client | CLAUDE_API_CLIENT | Configured Claude API client instance |

## Notes

- API key resolution order: ComfyUI Settings > node widget > config.ini
- Sonnet 5 is the default and offers the best balance of performance and cost
- Haiku 4.5 is fastest and cheapest; Opus 4.8 is most capable
- Sonnet 5, Opus 4.8, and Opus 4.7 reject temperature/top_p/top_k (the client omits them automatically); Fable 5 accepts them
- Prompt caching is enabled by default and significantly reduces costs for repeated system prompts
