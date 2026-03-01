<!-- ABOUTME: Help documentation for the Claude Conversation ComfyUI node. -->
<!-- ABOUTME: Manages multi-turn conversations with Claude, preserving message history. -->

# Claude Conversation

Maintains a multi-turn conversation with Claude, preserving message history across executions. Chain multiple conversation nodes to build dialogues.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String (multiline) | (empty) | Your message in the conversation |
| client | CLAUDE_API_CLIENT | (none) | Claude API client (optional if API key is configured in Settings) |
| conversation_history | CLAUDE_CONVERSATION | (none) | Previous conversation state (optional). Connect from a previous Conversation node |
| system_prompt | String (multiline) | (empty) | System prompt, only used for new conversations (optional) |
| auto_trim | Boolean | True | Automatically trim old messages to fit context window (optional) |
| reset_conversation | Boolean | False | Start a new conversation, discarding history (optional) |
| temperature | Float | 0.7 | Creativity level (optional). Min: 0.0, Max: 1.0, Step: 0.05 |
| max_tokens | Int | 2048 | Maximum length of response (optional). Min: 256, Max: 4096, Step: 128 |

## Output

| Output | Type | Description |
|--------|------|-------------|
| response | String | Claude's response text |
| conversation_history | CLAUDE_CONVERSATION | Updated conversation state to pass to the next node |

## Notes

- Chain nodes by connecting conversation_history output to the next node's conversation_history input
- Auto-trim removes oldest messages first when approaching the 200k token context window
- The system prompt is only applied when starting a new conversation (no history or reset)
- Consecutive same-role messages are automatically consolidated for API compatibility
- Re-executes on every queue (not cached)
