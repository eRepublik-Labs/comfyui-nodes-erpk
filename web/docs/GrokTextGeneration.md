<!-- ABOUTME: Help documentation for the Grok Text Generation ComfyUI node. -->
<!-- ABOUTME: One-shot text completion via xAI's Grok chat API. -->

# Grok Text Generation

Sends a single prompt to xAI's Grok and returns the generated text. Stateless — for multi-turn dialog use Grok Chat instead.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | (empty) | Text prompt to send to Grok |
| client | GROK_API_CLIENT | — | Grok API client (optional if API key is in Settings) |
| model | Combo | grok-4.7 | Grok model. Options: grok-4.7, grok-4.20-0309-non-reasoning, grok-4.20-multi-agent-0309, grok-build-0.1 (optional) |
| temperature | Float | 0.7 | Creativity (0.0 focused → 2.0 very creative). Range: 0.0–2.0 (optional) |
| max_tokens | Int | 4096 | Maximum visible response tokens; reasoning tokens are not counted. Range: 256–128000. grok-4.20-multi-agent-0309 does not honour it (optional) |
| reasoning_effort | Combo | (model default) | Options: (model default), none, low, medium, high, xhigh. Only grok-4.7 receives it (low to xhigh; `none` is sent as `low` because grok-4.7 rejects it). The other models reject the field, so it is not sent to them. (model default) sends nothing (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| response | String | Generated text |

## Notes

- Re-executes on every queue (not cached) since API responses vary.
- For stateful conversation across multiple nodes, use **Grok Chat** which threads message history via a typed `GROK_CHAT_SESSION` output.
- Async-enabled — multiple Grok Text Generation nodes in the same workflow execute concurrently.
