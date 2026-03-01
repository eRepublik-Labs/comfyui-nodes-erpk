<!-- ABOUTME: Help documentation for the Claude Conversation Info ComfyUI node. -->
<!-- ABOUTME: Displays conversation statistics including message counts and token usage. -->

# Claude Conversation Info

Displays information about a conversation's state, including message counts and estimated token usage.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| conversation_history | CLAUDE_CONVERSATION | (required) | Conversation state to inspect |

## Output

| Output | Type | Description |
|--------|------|-------------|
| info | String | Formatted statistics: message counts, token estimate, and context window usage percentage |

## Notes

- Shows user message count, assistant message count, and total messages
- Estimates total tokens and displays context window usage as a percentage of 200k
- Indicates whether a system prompt is active
- This is an output node — it prints info to the ComfyUI console as well
- Connect to any Conversation node's conversation_history output to inspect its state
