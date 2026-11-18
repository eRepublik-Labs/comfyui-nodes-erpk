<!-- ABOUTME: Help documentation for the Grok Chat ComfyUI node. -->
<!-- ABOUTME: Multi-turn conversation with xAI Grok, threading history via GROK_CHAT_SESSION. -->

# Grok Chat

Maintains a multi-turn conversation by threading message history between Grok Chat nodes. Chain a Chat node's `chat_session` output into the next Chat node's `chat_session` input to continue the dialog.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | (empty) | Your message in the conversation |
| client | GROK_API_CLIENT | — | Grok API client (optional if API key is in Settings) |
| model | Combo | grok-4.7 | Grok model. Options: grok-4.7, grok-4.20-0309-non-reasoning, grok-4.20-multi-agent-0309, grok-build-0.1 (optional) |
| chat_session | GROK_CHAT_SESSION | — | Previous chat session output (optional). Leave disconnected to start fresh |
| reset_conversation | Boolean | false | Discard `chat_session` and start a new conversation (optional) |
| temperature | Float | 0.7 | Creativity. Range: 0.0–2.0 (optional) |
| max_tokens | Int | 4096 | Maximum visible response tokens; reasoning tokens are not counted. Range: 256–128000. A reply cut off at this limit raises an error instead of returning partial text. grok-4.20-multi-agent-0309 does not honour it (optional) |
| reasoning_effort | Combo | (model default) | Options: (model default), none, low, medium, high, xhigh. grok-4.7 receives it (low to xhigh; `none` is sent as `low` because grok-4.7 rejects it). On grok-4.20-multi-agent-0309 it sets `agent_count` instead: low/medium = 4 agents, high/xhigh = 16 agents (about 12x the prompt tokens of the default), `none` sends nothing. The other models reject the field, so it is not sent to them. (model default) sends nothing (optional) |
| system_prompt | String | (empty) | Instructions sent as a system message ahead of the conversation and stored in `chat_session`, so later turns keep them. A non-empty value replaces the system prompt of a connected session; an empty one keeps the session's, or sends none (optional) |
| seed | Int | -1 | 1 or more goes to xAI as the sampling seed (the same seed can still give a different reply). 0 and -1 send no seed. The control after the widget starts at `randomize`, so each queue gets a new seed and a fresh reply; set it to `fixed` to keep one. Range: -1 to 2147483647 (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| response | String | Grok's reply to this turn |
| chat_session | GROK_CHAT_SESSION | Updated session — feed into the next Grok Chat node to continue |

## Notes

- Full message history is sent on each turn (client-side state). Survives ComfyUI restarts and isn't subject to the xAI server-side 30-day response retention.
- To branch a conversation: connect the same `chat_session` to two downstream Chat nodes with different prompts.
- `reset_conversation=true` overrides any connected `chat_session` and starts over from the new prompt.
- Caching follows the seed. By default every queue calls Grok and bills again: -1 always re-runs, and the `randomize` control picks a new seed after each queue. With the control on `fixed` and any seed other than -1, re-queuing identical inputs reuses the cached reply and bills nothing. xAI rejects a seed of 0, so the node never sends 0 or -1.
