<!-- ABOUTME: Help documentation for the Alibaba WAN 2.7 Text-to-Video ComfyUI node. -->
<!-- ABOUTME: Generates video clips from text prompts using Alibaba WAN 2.7 via WaveSpeed AI. -->

# Alibaba WAN 2.7 Text-to-Video

Generates video clips from text prompts using Alibaba's WAN 2.7 model via the WaveSpeed AI API. Returns a URL to the generated video.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of the video to generate |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| negative_prompt | String | "" | Elements to exclude from the generated video (optional) |
| audio | String | "" | Optional audio URL used to guide generation (optional) |
| duration | Int | 5 | Clip length in seconds, 2-15 (optional) |
| aspect_ratio | Combo | 16:9 | Output aspect ratio: 16:9, 9:16, 1:1 (optional) |
| resolution | Combo | 720p | Output resolution: 720p or 1080p (optional) |
| enable_prompt_expansion | Boolean | false | Automatically enrich the prompt before generation (optional) |
| seed | Int | -1 | Random seed for reproducibility, -1 for random (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | STRING | URL of the generated video |

## Notes

- **API Docs:** [Alibaba WAN 2.7 Text-to-Video](https://wavespeed.ai/docs/docs-api/alibaba/alibaba-wan-2.7-text-to-video)
- Prompt is required and cannot be empty
- Video generation can take several minutes; the node polls every 10s with a 900s timeout
- Pass the `video_url` output into a `WaveSpeed Preview Video` node to download and preview the result
