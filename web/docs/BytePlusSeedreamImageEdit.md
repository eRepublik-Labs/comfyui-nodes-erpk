<!-- ABOUTME: Help documentation for the BytePlus Seedream Image Edit ComfyUI node. -->
<!-- ABOUTME: Seedream image generation on BytePlus ModelArk with the user's own API key. -->

# BytePlus Seedream Image Edit

Edits or combines reference images, or splits one image into layers, with Seedream on BytePlus ModelArk.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | (empty) | The edit to make. Optional for layer decomposition |
| images | IMAGE | none | Reference image batch, sent inline (JPEG, or PNG with alpha when you connect `mask`). Max 10 on 5.5/5.0 pro/5.0 flash, 14 on 5.0 lite/4.5/4.0, counted with `images_url` |
| images_url | String | (empty) | More reference images, one https URL or `data:image/` URI per line, after the batch. Any other line stops the run before the call |
| mask | MASK | none | Alpha for `images` in LoadImage convention (1 = transparent). 5.0 pro and flash need it for a transparent background: without it the image goes as JPEG, which has no alpha, and the node stops before the call. A Seedream `alpha` output is the inverse: pass it through InvertMask first |
| client | BYTEPLUS_API_CLIENT | none | BytePlus API Client (optional when the key is in Settings or config.ini) |
| model | Combo | dola-seedream-5-5-261028 | dola-seedream-5-5-261028, dola-seedream-5-0-pro-260628, dola-seedream-5-0-flash-260915, seedream-5-0-260128 (5.0 lite), seedream-4-5-251128, seedream-4-0-250828 |
| endpoint_id | String | (empty) | Custom ModelArk endpoint ID sent instead of the model ID. The model widget still decides which options apply |
| size | Combo | 2K | 1K/1.5K/2K on 5.5, 5.0 pro, 5.0 flash; 2K/3K/4K on 5.0 lite; 2K/4K on 4.5; 1K/2K/4K on 4.0. custom sends width x height. auto is for layer decomposition |
| width | Int | 2048 | Used when size is custom |
| height | Int | 2048 | Used when size is custom. Total pixels: 921,600-4,624,220 on 5.5/5.0 pro/5.0 flash; 3,686,400-16,777,216 on 5.0 lite and 4.5; 921,600-16,777,216 on 4.0. Every model also needs an aspect ratio within 1:16-16:1 |
| sequential | Combo | disabled | disabled, auto. auto returns a related set of up to max_images on 5.0 lite, 4.5 and 4.0 |
| max_images | Int | 15 | Upper bound for sequential auto (1-15); reference images plus max_images must be at most 15 |
| output_format | Combo | (model default) | png, jpeg. 5.5 defaults to png, 5.0 models to jpeg; 4.5 and 4.0 make jpeg only |
| background | Combo | (model default) | 5.5: auto, transparent, opaque. 5.0 pro and flash: opaque, transparent (from exactly one reference with alpha). Transparent needs png |
| optimize_prompt_mode | Combo | standard | standard, fast. fast on 5.0 pro and 4.0 only |
| response_format | Combo | url | url (downloaded by the node) or b64_json (inline) |
| watermark | Boolean | false | "AI-generated" mark. ModelArk's own default is on; the node sends off unless set |
| fail_on_partial | Boolean | true | When some images of a sequential batch fail moderation: raise (on), or return the rest and log the failures (off) |
| layer_decomposition | Boolean | false | 5.5, 5.0 pro, 5.0 flash: split one image (at least 262,144 pixels) into a base plus transparent layers. Size must be a preset or auto |
| layer_max_images | Int | 30 | 5.5 only: most images returned, base included (2-100). Rate limits reserve this count up front |
| text_recognition | Boolean | false | 5.5 layer decomposition only: rich-text OCR on text layers |
| safety_identifier | String | (empty) | Optional hashed end-user ID, max 64 characters. Sent to 5.5, 5.0 pro and 5.0 flash only |
| seed | Int | -1 | Cache control only and not sent, because ModelArk documents no Seedream seed. -1 re-runs every queue |

## Output

| Output | Type | Description |
|--------|------|-------------|
| images | IMAGE | The returned images as one batch. With layer decomposition: the base, then each layer on a base-sized canvas |
| alpha | MASK | Per-image alpha, 1 = opaque, 0 = transparent. Invert it (InvertMask) before a mask input that uses the LoadImage convention |

## Notes

- Before any call, the node checks the request against the selected model's row in `byteplus/byteplus_api/seedream.py` and raises a `ValueError` naming the model and the value when the model rejects it.
- The call is synchronous. ModelArk answers with the images, so there is no task to poll or cancel.
- The console logs the estimated cost at ModelArk's list price per image tier, plus priced input images (5.5: $0.008 each; 5.0 pro: first free, then $0.003).
- Result URLs are valid for 24 h; the node downloads them right away.
- Layer decomposition: any failed layer fails the whole request. 5.0 pro bills layers at $0.0225 / $0.045 per image.
- ModelArk returns each layer cropped to its bounding box; the node places it back on a base-sized canvas so the batch stacks and recomposes directly.
