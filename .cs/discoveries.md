# Discoveries & Notes

## Claude Nodes - Missing API Features (2026-02-09)

Explored the full Claude node architecture. Key gaps identified:

1. **~~No tool use / function calling~~** — Phase 1 (structured output) now implemented. `ClaudeToolDefinition` + `ClaudeStructuredOutput` nodes provide forced tool use for guaranteed JSON. Agentic loop (Phase 2) still missing.
2. **No extended thinking** — Another supported API feature not exposed in nodes.
3. **No agentic loop pattern** — No node that can run Claude in a call→tool→call→tool loop.
4. **Agent Teams (Claude Code CLI) is not usable from API** — It's a CLI orchestration feature, not an SDK/API. Multi-agent patterns would need to be built from scratch using the Anthropic Python SDK.

## Architecture Notes

- All providers (Claude, OpenAI, Gemini, WaveSpeed) follow the same pattern: `provider/`, `provider_api/client.py`, `provider_api/utils.py`
- Custom types: `CLAUDE_API_CLIENT`, `CLAUDE_CONVERSATION`, `OPENAI_API_CLIENT`, `GEMINI_API_CLIENT`
- 10 Claude nodes total: APIClient, TextGeneration, VisionAnalysis, Conversation, ConversationInfo, PromptEnhancer (51 styles), TokenCounter, UsageStats, ToolDefinition, StructuredOutput
- Models: claude-sonnet-4-5, claude-opus-4-6, claude-haiku-4-5
- Prompt caching supported via beta headers
- ComfyUI's node graph is a natural fit for multi-agent chaining (nodes already connect via dependency graph)
