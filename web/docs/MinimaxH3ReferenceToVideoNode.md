<!-- ABOUTME: Help documentation for the MiniMax H3 Reference-to-Video ComfyUI node. -->
<!-- ABOUTME: Generates video guided by up to 9 reference images, 3 videos and 3 audios via MiniMax's hosted H3. -->

# MiniMax H3 Reference-to-Video

Generates video guided by reference images, videos and audio, with native stereo audio, using MiniMax's hosted H3 endpoint.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String (multiline) | (empty) | Prompt citing each reference by bracket tag. See below |
| reference_images_url | String | (empty) | Reference image URL(s), up to 9 (optional) |
| reference_videos_url | String | (empty) | Reference video URL(s), up to 3, combined 15s cap (optional) |
| reference_audios_url | String | (empty) | Reference audio URL(s), up to 3; cannot be used alone (optional) |
| reference_images | IMAGE | (none) | Reference images as a ComfyUI IMAGE batch, capped at 9. Takes precedence over reference_images_url (optional) |
| client | WAVESPEED_AI_API_CLIENT | (none) | WaveSpeed API client (optional if API key is in Settings) |
| duration | Int | 5 | Video duration in seconds. Range: 4-15 (optional) |
| aspect_ratio | Combo | 16:9 | 16:9, 9:16, 1:1, 4:3, 3:4, 21:9 (optional) |
| resolution | Combo | 768p | 768p or 2k (optional) |
| seed | Int | -1 | Cache control only; never sent to the API (optional) |
| reference_video | VIDEO | (none) | A reference video, uploaded to WaveSpeed and cited as Video 1 (optional) |
| reference_audio | AUDIO | (none) | A reference audio track, encoded to MP3, uploaded and cited as Audio 1 (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | String | URL of the generated video, ready for Preview Anything |

## Which edition this calls

This node calls MiniMax's own hosted H3 endpoint on WaveSpeed (`minimax/h3/...`), not the open-weights edition WaveSpeed hosts itself (`wavespeed-ai/minimax-h3/...`). The hosted edition offers 768p and 2k, 4-15s clips, and takes no seed or LoRA parameters. The MiniMax H3 Text-to-Image, Image Edit, Video Edit, Video Extend and LoRA Stack nodes still use the open-weights edition.

## The seed is cache control only

The endpoint documents no seed, so the widget is never sent. A fixed seed lets ComfyUI reuse the video you already paid for; -1 generates again on every queue.

## There is no audio toggle

Audio is generated natively in one pass and steered by an `Audio:` line in the prompt, for example:

```
A lighthouse in a storm, slow dolly in.
Audio: waves crashing, wind, a distant foghorn.
```

## You must cite references by tag

The prompt must name each reference with its bracket tag: `<Picture 1>` to `<Picture 9>`, `<Video 1>` to `<Video 3>`, `<Audio 1>` to `<Audio 3>`. A reference mentioned only in plain text is ignored by the model. At least one reference image or video is required; audio cannot be supplied alone.

## Cost

| Item | Rate |
|------|------|
| Output at 768p | $0.10 / second |
| Output at 2k | $0.14 / second |
| Reference video | billed at the output rate per normalised second (each clip 2-15s, combined cap 15s) |
| Reference images | first 5 free, then $0.05 each |
| Reference audio | free |

WaveSpeed's worked example: 5 seconds of normalised reference video plus 5 seconds of output costs $1.00 at 768p or $1.40 at 2k.

## Connecting media instead of URLs

The API only ever receives URLs, so each kind of reference has two ways in.

| Kind | Typed input | URL fallback | How it travels |
|------|-------------|--------------|----------------|
| Images | reference_images (IMAGE batch, up to 9) | reference_images_url | Inlined as base64 data URIs |
| Video | reference_video (one VIDEO) | reference_videos_url (up to 3) | Uploaded to WaveSpeed, sent as a URL |
| Audio | reference_audio (one AUDIO) | reference_audios_url (up to 3) | Encoded to MP3, uploaded, sent as a URL |

A connected IMAGE batch replaces the image URL field entirely. A connected VIDEO or AUDIO is prepended to its URL list instead, so it becomes Video 1 or Audio 1 and any URLs you also supply follow it. The sockets carry one file each; use the URL fields for the second and third.

Video is uploaded in whatever container it already has rather than re-encoded, so nothing is lost and no generation-length wait is added.

## Notes

- Polling times out after 20 minutes on this node; reference runs take longer than text or image ones
- Workflows saved with the earlier 480p/540p/1080p tiers or the 9:21 ratio are remapped on load (480p/540p to 768p, 1080p to 2k, 9:21 to 9:16)
