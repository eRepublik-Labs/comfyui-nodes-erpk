<!-- ABOUTME: Help documentation for the Claude Vision Analysis ComfyUI node. -->
<!-- ABOUTME: Analyzes images using Claude's multimodal vision capabilities. -->

# Claude Vision Analysis

Analyzes images using Claude's multimodal vision capabilities. Supports single or batch images with configurable detail levels.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | IMAGE | (required) | Images to analyze. The node sends every image in the batch |
| question | String (multiline) | Describe this image in detail. | Question or instruction about the image(s) |
| client | CLAUDE_API_CLIENT | (none) | Claude API client (optional if API key is configured in Settings) |
| model | Combo | (inherit from client) | Override the client's model for this vision call (optional). Options: (inherit from client), claude-sonnet-5-5, claude-sonnet-5, claude-opus-5-5, claude-opus-5, claude-fable-5-1, claude-fable-5, claude-haiku-5-5 |
| additional_images | IMAGE | (none) | Additional images, sent after the primary batch (optional). Up to 600 images in total |
| detail_level | Combo | high | Level of detail in analysis (optional). Options: low, medium, high |
| max_tokens | Int | 8192 | Maximum length of analysis; thinking counts toward it (optional). Min: 256, Max: 128000, Step: 128 |
| seed | Int | -1 | Cache control. A fixed seed reuses the previous result; -1 re-runs every queue (optional) |
| effort | Combo | (model default) | How much effort Claude spends: thinking depth, tool calls and answer length (optional). Options: (model default), low, medium, high, xhigh, max. (model default) sends nothing, so the model keeps its own default (high; medium on Opus 5.5 and Haiku 5.5). Higher levels cost more tokens and time |

## Output

| Output | Type | Description |
|--------|------|-------------|
| analysis | String | Detailed image analysis text |

## Notes

- Sends every image in both batches, up to 600 in total; more than 600 raises an error naming the count
- The node resizes an image to fit 8000px on its longest side, or 3000px when the request has more than 20 images
- An image over 10 MB of base64 (a PNG of about 7.86 MB) raises an error naming its size, and the node sends nothing
- Detail levels control how thorough the analysis is: low = concise, high = comprehensive
- Use cases: image captioning, prompt reverse-engineering, quality assessment, data extraction
- Caching follows the seed: a fixed seed reuses the analysis you already paid for, while -1 (randomize) re-runs on every queue
- Every offered model accepts images up to 2576px on the long edge
- A reply cut off at `max_tokens` raises an error asking you to raise `max_tokens` instead of returning partial text. Thinking counts toward `max_tokens`, so a low value can be used up before any text is written
