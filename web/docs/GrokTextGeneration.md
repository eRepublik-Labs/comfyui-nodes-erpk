<!-- ABOUTME: Help documentation for the Grok Text Generation ComfyUI node. -->
<!-- ABOUTME: One-shot text completion via xAI's Grok chat API. -->

# Grok Text Generation

Sends a single prompt to xAI's Grok and returns the generated text. Stateless — for multi-turn dialog use Grok Chat instead.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | (empty) | Text prompt to send to Grok |
| client | GROK_API_CLIENT | — | Grok API client (optional if API key is in Settings) |
| model | Combo | grok-4.5 | Grok model. Options: grok-4.5, grok-4.3, grok-4.20-0309-reasoning, grok-4.20-0309-non-reasoning, grok-4.20-multi-agent-0309, grok-build-0.1 (optional) |
| temperature | Float | 0.7 | Creativity (0.0 focused → 2.0 very creative). Range: 0.0–2.0 (optional) |
| max_tokens | Int | 4096 | Maximum response tokens. Range: 256–16384 (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| response | String | Generated text |

## Notes

- Re-executes on every queue (not cached) since API responses vary.
- For stateful conversation across multiple nodes, use **Grok Chat** which threads message history via a typed `GROK_CHAT_SESSION` output.
- Async-enabled — multiple Grok Text Generation nodes in the same workflow execute concurrently.
