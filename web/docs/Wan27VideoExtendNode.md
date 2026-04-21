<!-- ABOUTME: Help documentation for the Alibaba WAN 2.7 Video Extend ComfyUI node. -->
<!-- ABOUTME: Extends an existing video clip with a continuation prompt via WaveSpeed AI. -->

# Alibaba WAN 2.7 Video Extend

Extends an existing video clip with a continuation prompt using Alibaba's WAN 2.7 model via the WaveSpeed AI API. Returns a URL to the extended video.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of the continuation |
| video_url | String | "" | Source video URL to extend |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| negative_prompt | String | "" | Elements to exclude from the generated video (optional) |
| audio | String | "" | Optional audio URL used to guide generation (optional) |
| extend_duration | Int | 5 | Length of the extension in seconds, 2-15 (optional) |
| resolution | Combo | 720p | Output resolution: 720p or 1080p (optional) |
| enable_prompt_expansion | Boolean | false | Automatically enrich the prompt before generation (optional) |
| seed | Int | -1 | Random seed for reproducibility, -1 for random (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | STRING | URL of the extended video |

## Notes

- **API Docs:** [Alibaba WAN 2.7 Video Extend](https://wavespeed.ai/docs/docs-api/alibaba/alibaba-wan-2.7-video-extend)
- Both `prompt` and `video_url` are required
- The `video_url` input maps to the WAN 2.7 request's `video` field internally
- Video generation can take several minutes; the node polls every 10s with a 900s timeout
- Pass the output into a `WaveSpeed Preview Video` node to download and preview the extended clip
- Chain with `Wan27TextToVideoNode` or `Wan27ImageToVideoNode` to iteratively build longer clips
