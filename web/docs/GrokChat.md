<!-- ABOUTME: Help documentation for the Grok Chat ComfyUI node. -->
<!-- ABOUTME: Multi-turn conversation with xAI Grok, threading history via GROK_CHAT_SESSION. -->

# Grok Chat

Maintains a multi-turn conversation by threading message history between Grok Chat nodes. Chain a Chat node's `chat_session` output into the next Chat node's `chat_session` input to continue the dialog.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | (empty) | Your message in the conversation |
| client | GROK_API_CLIENT | — | Grok API client (optional if API key is in Settings) |
| model | Combo | grok-4.5 | Grok model (optional) |
| chat_session | GROK_CHAT_SESSION | — | Previous chat session output (optional). Leave disconnected to start fresh |
| reset_conversation | Boolean | false | Discard `chat_session` and start a new conversation (optional) |
| temperature | Float | 0.7 | Creativity. Range: 0.0–2.0 (optional) |
| max_tokens | Int | 4096 | Maximum response tokens. Range: 256–16384 (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| response | String | Grok's reply to this turn |
| chat_session | GROK_CHAT_SESSION | Updated session — feed into the next Grok Chat node to continue |

## Notes

- Full message history is sent on each turn (client-side state). Survives ComfyUI restarts and isn't subject to the xAI server-side 30-day response retention.
- To branch a conversation: connect the same `chat_session` to two downstream Chat nodes with different prompts.
- `reset_conversation=true` overrides any connected `chat_session` and starts over from the new prompt.
