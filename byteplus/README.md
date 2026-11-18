# BytePlus ModelArk API Integration for ComfyUI

Seedance video and Seedream image generation called directly on BytePlus ModelArk with your own API key, over plain HTTPS. The nodes need no Comfy account, proxy or credits; ModelArk bills your BytePlus account.

**Version:** 2026.11.8
**Category in ComfyUI:** `ERPK/BytePlus` and `ERPK/BytePlus/Video`
**Requirements:** `requests` and `Pillow`, both already required by the pack. The provider adds no SDK dependency.
**Region:** `ap-southeast-1` (Johor), `https://ark.ap-southeast.bytepluses.com/api/v3`. Keys and model activation are per region, and Johor is the only region whose docs list both Seedance and Seedream.

## Nodes

| Node | ID | Output |
|------|----|--------|
| BytePlus API Client | `BytePlusAPIClient` | `BYTEPLUS_API_CLIENT` (optional config node) |
| BytePlus Seedance Text to Video | `BytePlusSeedanceTextToVideo` | `video_url`, `last_frame_url`, `task_id` |
| BytePlus Seedance Image to Video | `BytePlusSeedanceImageToVideo` | `video_url`, `last_frame_url`, `task_id` |
| BytePlus Seedance Reference to Video | `BytePlusSeedanceReferenceToVideo` | `video_url`, `last_frame_url`, `task_id` |
| BytePlus Seedance Task Result | `BytePlusSeedanceTaskResult` | `video_url`, `last_frame_url`, `status` |
| BytePlus Seedream Text to Image | `BytePlusSeedreamTextToImage` | `images` (`IMAGE`), `alpha` (`MASK`) |
| BytePlus Seedream Image Edit | `BytePlusSeedreamImageEdit` | `images` (`IMAGE`), `alpha` (`MASK`) |

Video nodes output URL strings, like the pack's other video nodes. Chain `video_url` into **WaveSpeed Preview Video** (`PreviewVideo`) or **Preview Anything** to save or view it. ModelArk keeps result URLs for 24 hours, and a Seedance 2.5 URL allows at most 100 downloads.

Help for every parameter is in `web/docs/<node id>.md` and in each widget's tooltip.

## Models

### Seedance (video)

| Model ID | Text | First frame | First + last | Ref images / videos / audio | Resolutions | Duration (s) | Only here |
|---|---|---|---|---|---|---|---|
| `dreamina-seedance-2-5-260628` | Y | Y | Y | 30 / 10 / 10 | 480p, 720p, 1080p, 4k | 4-30 or -1 | draft, mov |
| `dreamina-seedance-2-5-flash-261115` | Y | Y | Y | 10 / 5 / 5 | 480p, 720p | 4-30 or -1 | mov |
| `dreamina-seedance-2-0-260128` | Y | Y | Y | 9 / 3 / 3 | 480p, 720p, 1080p, 4k | 4-15 or -1 | |
| `dreamina-seedance-2-0-fast-260128` | Y | Y | Y | 9 / 3 / 3 | 480p, 720p | 4-15 or -1 | |
| `dreamina-seedance-2-0-mini-260615` (default) | Y | Y | Y | 9 / 3 / 3 | 480p, 720p | 4-15 or -1 | |
| `seedance-1-0-pro-250528` | Y | Y | Y | none | 480p, 720p, 1080p | 2-12 | seed, camera_fixed, frames, flex |
| `seedance-1-0-pro-fast-251015` | Y | Y | N | none | 480p, 720p, 1080p | 2-12 | seed, camera_fixed, frames, flex |

Every model outputs 24 fps; ModelArk has no fps parameter. `generate_audio` and `priority` apply to 2.x only. `return_last_frame`, `watermark`, `execution_expires_after` and `safety_identifier` apply to every model.

### Seedream (image)

| Model ID | Max refs | Size presets | Custom size (total pixels) | Sequential batch | Layers | Transparent output |
|---|---|---|---|---|---|---|
| `dola-seedream-5-5-261028` (default) | 10 | 1K, 1.5K, 2K | 921,600-4,624,220 | N | base + up to 99, text recognition | from text or references |
| `dola-seedream-5-0-pro-260628` | 10 | 1K, 1.5K, 2K | 921,600-4,624,220 | N | base + up to 16 | from one reference with alpha |
| `dola-seedream-5-0-flash-260915` | 10 | 1K, 1.5K, 2K | 921,600-4,624,220 | N | base + up to 16 | from one reference with alpha |
| `seedream-5-0-260128` (5.0 lite) | 14 | 2K, 3K, 4K | 3,686,400-16,777,216 | up to 15 | N | N |
| `seedream-4-5-251128` | 14 | 2K, 4K | 3,686,400-16,777,216 | up to 15 | N | N, JPEG only |
| `seedream-4-0-250828` | 14 | 1K, 2K, 4K | 921,600-16,777,216 | up to 15 | N | N, JPEG only |

A custom size must also keep width / height within 1:16-16:1 on every model. Size `auto` exists only for layer decomposition, so only Image Edit offers it.

The `dola-` prefix on the 5.x IDs follows the ModelArk model list. ComfyUI's own partner nodes send the IDs without it.

## Which options reach the request

Each model's capabilities live in one table, in `byteplus_api/seedance.py` and `byteplus_api/seedream.py`. Before any call, the node builds the request from that table.

- An option the selected model cannot honour, and that would change the result or the price, stops the run with a `ValueError` naming the model and the value. Examples: a resolution the model lacks, reference inputs on Seedance 1.0, a last frame on 1.0 pro fast, `flex` on 2.x, `draft` off 2.5, a PNG request to Seedream 4.5, a size preset the model lacks.
- Seedance 2.5 first-frame and first+last-frame tasks accept only `ratio` adaptive. The node raises on any other ratio instead of changing it for you; the widget defaults to adaptive.
- The node leaves out a toggle the model ignores: `generate_audio` on 1.0, `camera_fixed`, `seed` and `frames` on 2.x, `priority` on 1.0, `omni_reference_task_type` on 2.0, `safety_identifier` on Seedream 5.0 lite, 4.5 and 4.0.

## Seed

ModelArk documents a request seed for Seedance 1.0 only, and for no Seedream model. On Seedance 1.0 the node sends a seed of 0 or more. Everywhere else the seed is cache control only and stays local: -1 (randomize) runs a new, billed generation on every queue, and a fixed value lets ComfyUI reuse the result it already paid for.

## Seedance 2.5 drafts

1. Turn on `draft` at 480p. ModelArk bills the draft as a normal 480p video.
2. Connect the draft's `task_id` output to `draft_task_id` on another Seedance node, or paste it.
3. Clear the prompt, disconnect every image, video and audio input, and pick 1080p or 4k.

The final render reuses the draft's prompt, inputs, duration, ratio, seed and audio setting, so the node sends none of them. Draft IDs stay valid for 14 days.

## Media

- Images connected to the nodes go inline as base64 (JPEG quality 95, or a lossless PNG when a mask supplies alpha). Seedance checks 300-6000 px per side and an aspect ratio of 0.4-2.5; Seedream checks its own limits. Each image must encode under 30 MB, and the whole request under 64 MB.
- Reference videos and audio for Seedance Reference to Video are URL strings you host, one per line. ModelArk accepts video only as a URL or `asset://ID`, never inline.
- Every image input also has a URL field. Use it for `asset://ID` portrait assets and for your own earlier Seedance or Seedream outputs, which ModelArk trusts for 30 days. Seedance 2.x rejects real human faces otherwise (`InputImageSensitiveContentDetected.PrivacyInformation`).

## Cancel and errors

- Pressing Cancel in ComfyUI checks the task. The node deletes a `queued` task, which makes ModelArk cancel it. ModelArk cannot cancel a `running` task, so it finishes and bills; the node stops waiting and says so. If the task had already succeeded, the node prints its video URL.
- **BytePlus Seedance Task Result** reads a task back by ID for free. Give it the `task_id` of a run you cancelled or lost to collect the billed video. Task IDs stay valid for 7 days.
- Task failures (`failed`, `expired`, `cancelled`) raise with ModelArk's error code and message, including moderation codes such as `OutputVideoSensitiveContentDetected`. ModelArk does not bill failed or moderated generations.
- A rejected request raises `ModelArk POST ... returned HTTP <status> <code>: <message>`.
- Task creation is never retried, so a network error cannot start a second billed task. Status polling retries through connection errors, 429 and 5xx.
- After each run the console shows the tokens or images used and the estimated cost from ModelArk's price list.
- A Seedream image is billed once ModelArk returns it, so the node never discards one. A partial batch (some images refused by moderation) returns the rest and logs the refusals; with `fail_on_partial` on it raises instead. Before any raise after ModelArk answered, the node saves every decoded image as PNG in ComfyUI's `output/byteplus_recovered` and names the files in the error.
- Seedream images of different sizes in one response are letterboxed onto the largest, centered, with bars the `alpha` output marks transparent.

## Installation

1. Create an API key in the BytePlus console under ModelArk > API Keys for region `ap-southeast-1`.
2. Activate each model you want on the Model activation page. Seedance 2.0 and 2.5 activation needs a balance, savings plan or resource pack of at least 30 US dollars.
3. Configure the key (priority order, first non-empty wins):
   1. **ComfyUI Settings** (recommended), under Settings > ERPK > API Keys > BytePlus ModelArk API Key. Workflows never store keys set here.
   2. **Widget input**, the `api_key` field on the BytePlus API Client node.
   3. **Config file**, by uncommenting `BYTEPLUS_API_KEY` in `byteplus/config.ini`.

Environment variables are not read.

If your account returns `InvalidEndpointOrModel.ModelIDAccessDisabled`, create a custom endpoint in the console and put its ID in the node's `endpoint_id` field.

## Not exposed

- `callback_url` (webhooks), because the node polls instead.
- `stream` (Seedream server-sent events), because it only changes how the same images arrive.
- `fps` and `guidance_scale`, because ModelArk documents neither for current models.
