<!-- ABOUTME: Help documentation for the Gemini System Instruction ComfyUI node. -->
<!-- ABOUTME: Sets a system-level instruction to guide Gemini model behavior. -->

# Gemini System Instruction

Sets a system-level instruction that persists across all subsequent requests for a Gemini client. Use this to guide the model's tone, format, or domain focus.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| client | GEMINI_API_CLIENT | - | Gemini API client to configure |
| system_instruction | String | "" | System-level instruction to guide model behavior |

## Output

| Output | Type | Description |
|--------|------|-------------|
| client | GEMINI_API_CLIENT | Client with the system instruction applied |

## Notes

- System instructions persist for all requests made with the returned client
- Place this node between Gemini API Config and generation nodes in your workflow
- Example instructions: "Respond in JSON format", "Use a casual tone", "Focus on technical accuracy"
