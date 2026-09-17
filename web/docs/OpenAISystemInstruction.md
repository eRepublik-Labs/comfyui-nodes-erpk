<!-- ABOUTME: Help documentation for the OpenAI System Instruction ComfyUI node. -->
<!-- ABOUTME: Sets a system-level instruction for an OpenAI client. -->

# OpenAI System Instruction

Sets a system-level instruction that persists across all requests for an OpenAI client. Use this to guide model behavior for downstream nodes.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| client | OPENAI_API_CLIENT | — | OpenAI API client to configure |
| system_instruction | String | (empty) | System-level instruction to guide model behavior |

## Output

| Output | Type | Description |
|--------|------|-------------|
| client | OPENAI_API_CLIENT | Configured client with system instruction applied |

## Notes

- Connect this between an API Config node and generation nodes to set persistent behavior
- The system instruction applies to all subsequent requests made through this client
- Empty instructions are ignored

## Which nodes it reaches

| Node | Effect |
|------|--------|
| OpenAI Text Generation, Chat, Vision | Sent as a system message |
| OpenAI Image via Responses | Sent as the Responses API instructions parameter, steering the mainline model |
| OpenAI Image Generation, Image Edit | **No effect.** The images endpoint accepts only a prompt, with no system or instructions field |

Those two image nodes still accept a configured client, because the client also carries the API key. Put the guidance in their prompt instead.
