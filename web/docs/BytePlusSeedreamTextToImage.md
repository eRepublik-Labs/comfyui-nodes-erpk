<!-- ABOUTME: Help documentation for the BytePlus Seedream Text to Image ComfyUI node. -->
<!-- ABOUTME: Seedream image generation on BytePlus ModelArk with the user's own API key. -->

# BytePlus Seedream Text to Image

Generates images from a text prompt with Seedream, called directly on BytePlus ModelArk with your own key.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | (empty) | What the image shows |
| client | BYTEPLUS_API_CLIENT | none | BytePlus API Client (optional when the key is in Settings or config.ini) |
| model | Combo | dola-seedream-5-5-261028 | dola-seedream-5-5-261028, dola-seedream-5-0-pro-260628, dola-seedream-5-0-flash-260915, seedream-5-0-260128 (5.0 lite), seedream-4-5-251128, seedream-4-0-250828 |
| endpoint_id | String | (empty) | Custom ModelArk endpoint ID sent instead of the model ID. The model widget still decides which options apply |
| size | Combo | 2K | 1K/1.5K/2K on 5.5, 5.0 pro, 5.0 flash; 2K/3K/4K on 5.0 lite; 2K/4K on 4.5; 1K/2K/4K on 4.0. custom sends width x height |
| width | Int | 2048 | Used when size is custom |
| height | Int | 2048 | Used when size is custom. Total pixels: 921,600-4,624,220 on 5.5/5.0 pro/5.0 flash; 3,686,400-16,777,216 on 5.0 lite and 4.5; 921,600-16,777,216 on 4.0. Every model also needs an aspect ratio within 1:16-16:1 |
| sequential | Combo | disabled | disabled, auto. auto returns a related set of up to max_images on 5.0 lite, 4.5 and 4.0 |
| max_images | Int | 15 | Upper bound for sequential auto (1-15); reference images plus max_images must be at most 15 |
| output_format | Combo | (model default) | png, jpeg. 5.5 defaults to png, 5.0 models to jpeg; 4.5 and 4.0 make jpeg only |
| background | Combo | (model default) | 5.5: auto, transparent, opaque. 5.0 pro and flash: opaque, transparent (from exactly one reference with alpha). Transparent needs png |
| optimize_prompt_mode | Combo | standard | standard, fast. fast on 5.0 pro and 4.0 only |
| response_format | Combo | url | url (downloaded by the node) or b64_json (inline) |
| watermark | Boolean | false | "AI-generated" mark. ModelArk's own default is on; the node sends off unless set |
| fail_on_partial | Boolean | false | When some images of a sequential batch fail moderation: return the rest and log which were refused and why (off), or raise after saving the billed images to `output/byteplus_recovered` (on) |
| safety_identifier | String | (empty) | Optional hashed end-user ID, max 64 characters. Sent to 5.5, 5.0 pro and 5.0 flash only |
| seed | Int | -1 | Cache control only and not sent: Seedream echoes a seed but two identical requests still return different images (measured on 5.0 flash). -1 re-runs every queue |

## Output

| Output | Type | Description |
|--------|------|-------------|
| images | IMAGE | The returned images as one batch |
| alpha | MASK | Per-image alpha, 1 = opaque, 0 = transparent. Invert it (InvertMask) before a mask input that uses the LoadImage convention |

## Notes

- Before any call, the node checks the request against the selected model's row in `byteplus/byteplus_api/seedream.py` and raises a `ValueError` naming the model and the value when the model rejects it.
- The call is synchronous. ModelArk answers with the images, so there is no task to poll or cancel.
- The console logs the estimated cost at ModelArk's list price per image tier, plus priced input images (5.5: $0.008 each; 5.0 pro: first free, then $0.003).
- Result URLs are valid for 24 h; the node downloads them right away.
- ModelArk bills every image it returns. Every image that downloads and decodes is either output by the node or saved as PNG in ComfyUI's `output/byteplus_recovered` folder, with the files named in the error or the console. That covers a raise after ModelArk answered (a partial batch with `fail_on_partial` on, an image that does not decode, a layer that cannot be placed) and a run ComfyUI stopped while the request was in flight. An image that does not download or decode cannot be saved; URL results are printed, valid 24 hours.
- Images of different sizes in one response are letterboxed onto the largest width and height, centered, with mid-grey bars that the `alpha` output marks transparent. The Image Grid Loader handles mixed sizes the same way.
- 5.5 makes transparent images from text alone; 5.0 pro and flash need Image Edit with one reference that carries alpha.
