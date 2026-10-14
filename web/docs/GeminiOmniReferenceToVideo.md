<!-- ABOUTME: Help documentation for the Gemini Omni Reference to Video ComfyUI node. -->
<!-- ABOUTME: Generates video featuring the subjects in reference images via Gemini Omni Flash. -->

# Gemini Omni Reference to Video

Generates 3-10 second video at 24 FPS, 360p to 4k, that features the people, objects or style shown in one or more reference images. Uses Gemini Omni Flash 1.1 (`gemini-omni-1.1-flash`) with the `reference_to_video` task.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | What the video should show. Cite references in batch order as `<IMAGE_REF_0>`, `<IMAGE_REF_1>`, ... |
| reference_images | Image | - | Reference images, sent in batch order. Use Batch Images to combine several |
| client | GEMINI_API_CLIENT | - | Gemini API client. Optional when the key is in ComfyUI Settings |
| aspect_ratio | Combo | 16:9 | Video aspect ratio: 16:9 or 9:16 (optional) |
| resolution | Combo | 720p | Output resolution: 360p, 720p, 1080p or 4k. 1080p and 4k are upscaled by Google and need a stored interaction, so the node downloads, then deletes, the file (optional) |
| output_directory | String | "" | Directory to save video. Empty uses ComfyUI output folder (optional) |
| seed | Int | -1 | Cache control only — never sent to the API. Range: -1 to 4294967295 (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_path | String | File path to the generated .mp4 video |

## Prompting references

Google's guide uses tags to tie each image to a role: `A cat <IMAGE_REF_0> playfully bats at a ball of yarn <IMAGE_REF_1>`. Tags count from 0 in the order the images arrive in the batch.

## Notes

- The seed works as on Gemini Omni Video Generation: a fixed seed reuses the video you already paid for, -1 generates again on every queue
- 1080p and 4k come back through the Files API (URI delivery) because they exceed the 4MB inline limit; the node waits up to 10 minutes for the file
- Uploading images that contain minors is not supported in the EEA, Switzerland and the UK, and images of certain recognizable people are rejected
- Negative prompts, system instructions, temperature and top_p are not supported; state exclusions in the prompt

## Pricing

$1.50 per 1M input tokens, and roughly $0.10 per second of generated video at 720p.
