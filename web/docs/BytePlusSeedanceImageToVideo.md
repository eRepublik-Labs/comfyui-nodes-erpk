<!-- ABOUTME: Help documentation for the BytePlus Seedance Image to Video ComfyUI node. -->
<!-- ABOUTME: Seedance video generation on BytePlus ModelArk with the user's own API key. -->

# BytePlus Seedance Image to Video

Animates a start frame, optionally toward an end frame, with Seedance on BytePlus ModelArk.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | (empty) | Optional description of the motion |
| first_frame | IMAGE | none | Start frame (one image), sent inline as JPEG. 300-6000 px per side, aspect ratio 0.4-2.5. Takes precedence over `first_frame_url` |
| first_frame_url | String | (empty) | Start frame as an https URL or `asset://ID` |
| last_frame | IMAGE | none | End frame (one image). Not on 1.0 pro fast. Cropped to the start frame's aspect ratio if they differ |
| last_frame_url | String | (empty) | End frame as an https URL or `asset://ID` |
| client | BYTEPLUS_API_CLIENT | none | BytePlus API Client (optional when the key is in Settings or config.ini) |
| model | Combo | dreamina-seedance-2-0-mini-260615 | dreamina-seedance-2-5-260628, -2-5-flash-261115, -2-0-260128, -2-0-fast-260128, -2-0-mini-260615, seedance-1-0-pro-250528, seedance-1-0-pro-fast-251015 |
| endpoint_id | String | (empty) | Custom ModelArk endpoint ID sent instead of the model ID. Needed by accounts that get `ModelIDAccessDisabled`. The model widget still decides which options apply |
| resolution | Combo | 720p | 480p, 720p on every model; 1080p on 2.5, 2.0, 1.0; 4k on 2.5 and 2.0 |
| ratio | Combo | adaptive | adaptive, 16:9, 4:3, 1:1, 3:4, 9:16, 21:9. adaptive follows the start frame (a 1.0 pro fast run came back 4:3). 2.5 and 2.5 flash accept adaptive only here |
| duration | Int | 5 | Seconds. 2.5: 4-30; 2.0 series: 4-15; 1.0: 2-12. -1 lets a 2.x model pick |
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
- Cancel pressed before the node creates the task stops it before it calls ModelArk, so ModelArk bills nothing.
- Polling runs every 8 s. Cancel in ComfyUI deletes a `queued` task; ModelArk cannot cancel a `running` one, so it finishes and bills.
- The console prints the task ID as soon as ModelArk creates the task, even when ComfyUI stopped the run during the request. Every cancel outcome is printed too. Fetch the video of a stopped run with the BytePlus Seedance Task Result node.
- `failed`, `expired` and `cancelled` tasks raise with ModelArk's code and message, including moderation codes. Failed and moderated generations are not billed.
- The console logs the completion tokens and the estimated cost at ModelArk's list price.
- 2.5 1080p/4k and 2.0 4k come back as 10-bit HEVC, which some players and browsers cannot decode.
- On 2.5 and 2.5 flash, the ratio must stay adaptive. ModelArk fails other ratios after queueing, so the node refuses them up front.
- A ratio unlike the image's center-crops the image.
- Seedance 2.x rejects real human faces. Use an `asset://ID` portrait asset, or the original URL of your own Seedance or Seedream output, in the URL field.
