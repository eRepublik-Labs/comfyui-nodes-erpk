<!-- ABOUTME: Help documentation for the OpenAI Chat ComfyUI node. -->
<!-- ABOUTME: Multi-turn conversation with OpenAI models preserving message history. -->

# OpenAI Chat

Multi-turn conversation with OpenAI models. Preserves message history across turns by passing the chat session output back into the next node.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | (empty) | Your message in the conversation |
| client | OPENAI_API_CLIENT | — | OpenAI API client (optional if API key is in Settings) |
| model | Combo | gpt-4o | Model to use (optional) |
| chat_session | OPENAI_CHAT_SESSION | — | Previous chat session to continue (optional). Connect from previous chat node |
| reset_conversation | Boolean | False | Start a new conversation, discarding history (optional) |
| temperature | Float | 0.7 | Creativity level, 0.0–2.0 (optional) |
| max_tokens | Int | 4096 | Maximum response length (optional). Range: 256–16384 |
| top_p | Float | 1.0 | Nucleus sampling threshold, 1.0=disabled (optional). Range: 0.0–1.0 |
| stop_sequences | String | (empty) | Stop generation at these sequences, one per line (optional) |
| response_format | Combo | default | Output format: default or json_object (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| response | String | Assistant's reply to your message |
| chat_session | OPENAI_CHAT_SESSION | Updated conversation history for chaining |

## Notes

- Chain multiple Chat nodes by connecting chat_session output to the next node's chat_session input
- Use reset_conversation to clear history and start fresh
- The chat session contains the full message history (user + assistant turns)
