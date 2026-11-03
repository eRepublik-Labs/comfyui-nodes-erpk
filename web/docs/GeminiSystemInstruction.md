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

- System instructions persist for all requests made with the returned client, including image generation and editing
- An instruction written for text replies can make an image model refuse. Asked to end every reply with a token, Nano Banana 2.1 returned IMAGE_RECITATION for a prompt it drew without the instruction (one probe)
- Gemini Chat sends the instruction of the client connected to each Chat node, so connect this client to every Chat node in a chain
- Place this node between Gemini API Config and generation nodes in your workflow
- Example instructions: "Respond in JSON format", "Use a casual tone", "Focus on technical accuracy"
