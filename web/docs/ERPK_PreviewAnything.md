<!-- ABOUTME: Help documentation for the ERPK Preview Anything utility node. -->
<!-- ABOUTME: Previews text, markdown, URLs, images, video, audio, and GIFs with a download button. -->

# Preview Anything

Preview any value in the graph: strings, URLs to media, ComfyUI IMAGE tensors, AUDIO dicts, or any Python value. A Download button saves the rendered content to your computer.

The three settings below live in a collapsible **Options** panel on the node — click the Options bar to expand the styled controls. The Download / Copy buttons appear only once there is content to act on.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| value | * (any) | — | The value to preview. Connect any output. |
| display_type | Combo | auto | `auto` detects from the input. Force with `text`, `markdown`, `image`, `gif`, `video`, `audio`. |
| filename | String | preview | Base filename used when the Download button is clicked. |
| strip_metadata | Boolean | false | Re-encode image URL inputs to strip EXIF / ICC / XMP (GPS, camera info, timestamps) before download. Images only; IMAGE tensor inputs are already metadata-free. |

## How detection works

When `display_type` is `auto`:

- **IMAGE tensor** — saved to temp and displayed as an image.
- **AUDIO dict** (has `waveform` + `sample_rate`) — saved as WAV and played.
- **String that looks like a URL** — detected by file extension:
  - `.png .jpg .jpeg .webp .bmp .tiff .avif` → image
  - `.gif .apng` → gif
  - `.mp4 .webm .mov .m4v .mkv .ogv` → video
  - `.mp3 .wav .ogg .flac .m4a .aac .opus` → audio
  - Unknown extension → shown as text
- **String with markdown markers** (`#`, `*`, fenced code, links, lists) → rendered as markdown.
- **Anything else** — shown as plain text (dicts/lists are JSON-formatted).

## Download behavior

- For text/markdown: a Blob is created and downloaded with `.txt` or `.md`.
- For images/video/audio/gif: the URL is fetched and saved to disk. The original extension is preserved when possible.
- Cross-origin URLs that block CORS fall back to opening in a new tab.

## Notes

- The last rendered content is saved in the workflow, so the preview persists on reload.
- Use `display_type` to force a specific renderer (e.g. to see a JSON string rendered as markdown code).
- This is an output node: it always executes so the preview refreshes on every queue.
