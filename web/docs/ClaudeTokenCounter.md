<!-- ABOUTME: Help documentation for the Claude Token Counter ComfyUI node. -->
<!-- ABOUTME: Counts tokens in text and estimates Claude API costs. -->

# Claude Token Counter

Counts tokens in text and provides cost estimates for Claude API usage. Supports accurate API-based counting or local estimation.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| text | String (multiline) | (empty) | Text to count tokens for |
| model | Combo | claude-sonnet-4-6 | Model for token counting and cost estimation. Options: claude-sonnet-4-6, claude-opus-4-6, claude-haiku-4-5-20251001, claude-sonnet-4-5-20250929 |
| client | CLAUDE_API_CLIENT | (none) | Connect a client for accurate API-based counting (optional). Otherwise uses ~4 chars/token estimation |

## Output

| Output | Type | Description |
|--------|------|-------------|
| token_count | Int | Number of tokens in the text |
| summary | String | Formatted analysis with character count, token count, context usage, and cost estimates |

## Notes

- With a client connected: uses the Anthropic API for accurate token counts
- Without a client: estimates at ~4 characters per token
- Shows cost estimates for the text as both input and output tokens
- Warns when context usage exceeds 75% or 90% of the 200k window
- Pricing data is loaded from pricing.json and reflects current Anthropic rates
- This is an output node — it prints the summary to the ComfyUI console as well
