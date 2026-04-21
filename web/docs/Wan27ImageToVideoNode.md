<!-- ABOUTME: Help documentation for the Alibaba WAN 2.7 Image-to-Video ComfyUI node. -->
<!-- ABOUTME: Animates a source image into a video clip using Alibaba WAN 2.7 via WaveSpeed AI. -->

# Alibaba WAN 2.7 Image-to-Video

Animates a source image into a video clip using Alibaba's WAN 2.7 model via the WaveSpeed AI API. Optionally accepts an end-frame image for smooth transitions. Returns a URL to the generated video.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of the video to generate |
| image | String | "" | Source image URL (first frame of the video) |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| last_image | String | "" | Optional end-frame image URL for smooth transition (optional) |
| negative_prompt | String | "" | Elements to exclude from the generated video (optional) |
| audio | String | "" | Optional audio URL used to guide generation (optional) |
| duration | Int | 5 | Clip length in seconds, 2-15 (optional) |
| resolution | Combo | 720p | Output resolution: 720p or 1080p (optional) |
| enable_prompt_expansion | Boolean | false | Automatically enrich the prompt before generation (optional) |
| seed | Int | -1 | Random seed for reproducibility, -1 for random (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | STRING | URL of the generated video |

## Notes

- **API Docs:** [Alibaba WAN 2.7 Image-to-Video](https://wavespeed.ai/docs/docs-api/alibaba/alibaba-wan-2.7-image-to-video)
- Both `prompt` and `image` are required
- Aspect ratio is inferred from the source image; there is no explicit `aspect_ratio` input
- Video generation can take several minutes; the node polls every 10s with a 900s timeout
- Pass the `video_url` output into a `WaveSpeed Preview Video` node to download and preview the result
- Use `WaveSpeed Upload Image` to get a URL for a local image first
