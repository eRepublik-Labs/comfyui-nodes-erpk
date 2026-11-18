<!-- ABOUTME: Help documentation for the BytePlus Seedance Reference to Video ComfyUI node. -->
<!-- ABOUTME: Seedance video generation on BytePlus ModelArk with the user's own API key. -->

# BytePlus Seedance Reference to Video

Generates, edits or extends a video from reference images, videos and audio with Seedance 2.x on BytePlus ModelArk.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | (empty) | How to use the references. On 2.5, edit or extend wording makes the task an edit or extend |
| reference_images | IMAGE | none | Reference image batch, sent inline as JPEG. Max 30 (2.5), 10 (2.5 flash), 9 (2.0 series), counted with `reference_images_url` |
| reference_images_url | String | (empty) | More reference images, one https URL or `asset://ID` per line, after the batch |
| reference_videos_url | String | (empty) | Reference videos, one https URL or `asset://ID` per line. ModelArk takes no inline video. Max 10 / 5 / 3 |
| reference_audios_url | String | (empty) | Reference audio (wav, mp3), one https URL or `asset://ID` per line. Max 10 / 5 / 3. Audio alone works on 2.5 only |
| client | BYTEPLUS_API_CLIENT | none | BytePlus API Client (optional when the key is in Settings or config.ini) |
| model | Combo | dreamina-seedance-2-0-mini-260615 | dreamina-seedance-2-5-260628, -2-5-flash-261115, -2-0-260128, -2-0-fast-260128, -2-0-mini-260615, seedance-1-0-pro-250528, seedance-1-0-pro-fast-251015 |
| endpoint_id | String | (empty) | Custom ModelArk endpoint ID sent instead of the model ID. Needed by accounts that get `ModelIDAccessDisabled`. The model widget still decides which options apply |
| resolution | Combo | 720p | 480p, 720p on every model; 1080p on 2.5, 2.0, 1.0; 4k on 2.5 and 2.0 |
| ratio | Combo | adaptive | adaptive, 16:9, 4:3, 1:1, 3:4, 9:16, 21:9. A 2.5 video edit or extend accepts adaptive only |
| duration | Int | -1 | Seconds. 2.5: 4-30; 2.0 series: 4-15; 1.0: 2-12. -1 lets a 2.x model pick |
| frames | Int | 0 | 1.0 only: exact frame count 29-289, 25 + 4n, at 24 fps. Overrides duration. 0 = off; any other value with a 2.x model stops before the call |
| generate_audio | Boolean | true | 2.x only: synchronized stereo audio. Not sent to 1.0 |
| watermark | Boolean | false | "AI Generated" mark in the lower-right corner |
| return_last_frame | Boolean | false | Also return the final frame as a JPEG URL on `last_frame_url` |
| output_format | Combo | mp4 | mp4, mov. mov (H.264 yuv444p, PCM audio) on 2.5 and 2.5 flash only |
| camera_fixed | Boolean | false | 1.0 only: keep the camera still. On with a 2.x model stops before the call |
| service_tier | Combo | default | default, flex. flex runs offline at half price, 1.0 only |
| priority | Int | 0 | 2.x only: queue order 0-9 among tasks on the same endpoint. Not sent when 0 |
| draft | Boolean | false | 2.5 only: 480p preview billed as a 480p video. Its `task_id` feeds `draft_task_id` |
| draft_task_id | String | (empty) | Render this 2.5 draft at 1080p or 4k. Clear the prompt and disconnect every media input |
| omni_reference_task_type | Combo | auto | auto, reference, edit, extend. 2.5 only; not sent to 2.0. A 2.5 edit needs duration -1 and ratio adaptive |
| execution_expires_after | Int | 172800 | Seconds before ModelArk expires a task still queued or running (3600-259200) |
| safety_identifier | String | (empty) | Optional hashed end-user ID, max 64 characters |
| seed | Int | -1 | Sent on 1.0 when 0 or more. On 2.x cache control only and not sent: 2.x echoes a seed but two identical requests still return different videos (measured on 2.0 mini). -1 re-runs every queue; a fixed value reuses the cached video URL, which expires after 24 h |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | String | Video URL, valid 24 h (a 2.5 URL allows at most 100 downloads). Chain into WaveSpeed Preview Video or Preview Anything |
| last_frame_url | String | Final-frame JPEG URL when `return_last_frame` is on, else empty |
| task_id | String | ModelArk task ID. A draft's ID feeds `draft_task_id` |

## Notes

- Before any call, the node checks the request against the selected model's row in `byteplus/byteplus_api/seedance.py` and raises a `ValueError` naming the model and the value when the model rejects it.
- Polling runs every 8 s. Cancel in ComfyUI deletes a `queued` task; ModelArk cannot cancel a `running` one, so it finishes and bills.
- `failed`, `expired` and `cancelled` tasks raise with ModelArk's code and message, including moderation codes. Failed and moderated generations are not billed.
- The console logs the completion tokens and the estimated cost at ModelArk's list price.
- 2.5 1080p/4k and 2.0 4k come back as 10-bit HEVC, which some players and browsers cannot decode.
- 1.0 models take no references; the node refuses them.
- Video input bills at the lower with-video token rate, plus a minimum token charge whose table ModelArk keeps outside its docs. The logged cost ignores that minimum.
- Defaults (`duration` -1, `ratio` adaptive) follow ModelArk's advice for omni-reference tasks, because a 2.5 `auto` task can turn into an edit that needs them.
