<!-- ABOUTME: Help documentation for the Veo Text to Video ComfyUI node. -->
<!-- ABOUTME: Generates videos from text prompts using Google's Veo models. -->

# Veo Text to Video

Generates videos from text prompts using Google's Veo models. Veo 3+ models generate video with synchronized audio.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| client | GEMINI_API_CLIENT | - | Gemini API client from Gemini API Config node |
| prompt | String | "" | Text description of the video to generate (max 2500 characters) |
| model | Combo | veo-3.1-generate-preview | Veo model: veo-3.1-generate-preview, veo-3.1-fast-generate-preview, veo-3.0-generate-001, veo-3.0-fast-generate-001, veo-2.0-generate-001 (optional) |
| aspect_ratio | Combo | 16:9 | Video aspect ratio: 16:9 (landscape) or 9:16 (portrait) (optional) |
| duration_seconds | Combo | 8 | Video duration: 5, 6, 7, or 8 seconds (optional) |
| person_generation | Combo | allow_adult | Person generation safety: allow_adult, dont_allow, allow_all. Veo 3 only supports allow_all (optional) |
| enhance_prompt | Boolean | true | Let the model enhance your prompt for better results (optional) |
| negative_prompt | String | "" | Elements to exclude from the video (optional) |
| seed | Int | -1 | Random seed for reproducibility, -1 for random. Range: -1 to 4294967295 (optional) |
| output_directory | String | "" | Directory to save video. Empty uses ComfyUI output folder (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_path | String | File path to the generated .mp4 video |

## Notes

- Video generation is asynchronous and may take 2-10 minutes depending on duration and model
- Veo 3+ models generate synchronized audio along with video
- Veo 2 does not support audio generation
- The node polls every 20 seconds and times out after 40 minutes
- Pricing: $0.75 per second of video output for Veo 3+ models
