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
| temperature | Float | 0.7 | Ignored (optional). Current Claude models return an error for any temperature, so it is never sent; the widget stays so saved workflows load |
| max_tokens | Int | 2048 | Maximum length of response; thinking counts toward it (optional). Min: 256, Max: 128000, Step: 128 |
| model | Combo | (inherit from client) | Model override for this call (optional). Choose a model from the list, or inherit the connected client's model. Without a client, inherit means the Claude API client's default model |
| effort | Combo | (model default) | How much effort Claude spends: thinking depth, tool calls and answer length (optional). Options: (model default), low, medium, high, xhigh, max. (model default) sends nothing, so the model keeps its own default (high; medium on Opus 5.5). Higher levels cost more tokens and time |

## Output

| Output | Type | Description |
|--------|------|-------------|
| response | String | Claude's response text |
| conversation_history | CLAUDE_CONVERSATION | Updated conversation state to pass to the next node |

## Notes

- Chain nodes by connecting conversation_history output to the next node's conversation_history input
- Auto-trim removes oldest messages first when approaching the context window of the model this node calls (1M tokens on every offered model)
- The system prompt is only applied when starting a new conversation (no history or reset)
- Consecutive same-role messages are automatically consolidated for API compatibility
- Re-executes on every queue (not cached)
