<!-- ABOUTME: Help documentation for the Gemini Chat ComfyUI node. -->
<!-- ABOUTME: Multi-turn conversation with Gemini, preserving message history across nodes. -->

# Gemini Chat

Multi-turn conversation with Gemini that preserves message history. Chain multiple Chat nodes together to build conversations.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Your message in the conversation |
| client | GEMINI_API_CLIENT | - | Gemini API client (optional if API key is configured in Settings) |
| model | Combo | gemini-3.5-flash | Model to use: gemini-3.1-pro-preview, gemini-3.6-flash, gemini-3.5-flash, gemini-3.5-flash-lite, gemini-3-flash-preview, gemini-3.1-flash-lite, gemini-2.5-pro, gemini-2.5-flash, gemini-2.5-flash-lite (optional) |
| chat_session | GEMINI_CHAT_SESSION | - | Previous chat session from another Chat node (optional) |
| reset_conversation | Boolean | false | Start a new conversation, discarding history (optional) |
| temperature | Float | 0.7 | Creativity level, 0.0-2.0 (optional) |
| max_tokens | Int | 8192 | Maximum response length, 256-65536 (optional) |
| top_p | Float | 0.95 | Nucleus sampling threshold, 0.0=disabled (optional) |
| top_k | Int | 40 | Top-k sampling limit, 0=disabled (optional) |
| stop_sequences | String | "" | Stop generation at these sequences, one per line, max 5 (optional) |
| response_mime_type | Combo | default | Output format: default, text/plain, or application/json (optional) |
| response_schema | String | "" | JSON schema for structured output, used with application/json (optional) |
| thinking_level | Combo | none | Reasoning depth: none, low, medium, high. Gemini 3+ only (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| response | String | Chat response text |
| chat_session | GEMINI_CHAT_SESSION | Updated session to connect to the next Chat node |

## Notes

- Connect the chat_session output to the next Chat node's chat_session input to continue the conversation
- Use reset_conversation to start fresh while keeping the same client configuration
- A new session is automatically created if no chat_session input is provided
- Supports JSON mode for structured responses within conversations
