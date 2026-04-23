[Skip to main content](https://hyperframes.heygen.com/guides/hdr#content-area)

[HyperFrames home page![light logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/light.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=8fff06fe865e474513624008576b71bb)![dark logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/dark.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=5c0e7bb1b0c720593e3f904b47b9e1a3)](https://hyperframes.heygen.com/)

Search...

⌘KAsk AI

Search...

Navigation

Guides

HDR Rendering

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

Hyperframes can render to HDR10 MP4 (H.265 10-bit, BT.2020) when your composition references HDR video or HDR still images. HDR is opt-in via the `--hdr` flag — it auto-detects HDR sources and falls back to SDR when none are present.

The `--hdr` flag does not _force_ HDR. It enables HDR detection. If your composition contains only SDR media, the flag is a no-op and you get a normal SDR render.

## [​](https://hyperframes.heygen.com/guides/hdr\#quickstart)  Quickstart

1

[Navigate to header](https://hyperframes.heygen.com/guides/hdr#)

Add an HDR source to your composition

Hyperframes detects HDR from the source’s color space metadata. The most reliable HDR sources are:

- **HDR video** tagged BT.2020 with PQ (`smpte2084`) or HLG (`arib-std-b67`) transfer
- **HDR still images** as 16-bit PNG with BT.2020 PQ encoding

See [Source Media](https://hyperframes.heygen.com/guides/hdr#source-media-requirements) for full details.

2

[Navigate to header](https://hyperframes.heygen.com/guides/hdr#)

Render with --hdr

Terminal

```
npx hyperframes render --hdr --output output.mp4
```

HDR output requires `--format mp4`. If you also pass `--format mov` or `--format webm`, Hyperframes logs a warning and falls back to SDR.

3

[Navigate to header](https://hyperframes.heygen.com/guides/hdr#)

Verify the output is HDR

Use `ffprobe` to confirm the encoded stream carries HDR color tagging and HDR10 metadata:

Terminal

```
ffprobe -v error -show_streams output.mp4 | grep -E 'color_transfer|color_primaries|color_space'
```

See [Verifying HDR output](https://hyperframes.heygen.com/guides/hdr#verifying-hdr-output) for what to look for.

## [​](https://hyperframes.heygen.com/guides/hdr\#how-hdr-mode-works)  How HDR Mode Works

When `--hdr` is set, the producer:

1

[Navigate to header](https://hyperframes.heygen.com/guides/hdr#)

Probes every video and image source

Runs `ffprobe` on each `<video>` and `<img>` source to read its color space (primaries, transfer function, matrix). Probing is gated on `--hdr` to avoid `ffprobe` overhead on SDR-only renders.

2

[Navigate to header](https://hyperframes.heygen.com/guides/hdr#)

Picks the dominant HDR transfer

If any source uses PQ (`smpte2084`), the output uses **PQ**. Otherwise, if any source uses HLG (`arib-std-b67`), the output uses **HLG**. If no HDR sources are found, the flag is a no-op and you get an SDR render.

3

[Navigate to header](https://hyperframes.heygen.com/guides/hdr#)

Encodes to H.265 10-bit BT.2020

The video encoder switches to `libx265` with `-pix_fmt yuv420p10le`, color tagging `colorprim=bt2020:transfer=<smpte2084|arib-std-b67>:colormatrix=bt2020nc`, and HDR10 static metadata (`master-display` and `max-cll`). Without that metadata, players (QuickTime, YouTube, HDR TVs) tone-map the stream as if it were SDR BT.2020 — which looks wrong.

4

[Navigate to header](https://hyperframes.heygen.com/guides/hdr#)

Composites HDR sources natively, converts SDR overlays

HDR videos and images are extracted as 16-bit linear-light pixels via FFmpeg, kept out of the DOM screenshot, and composited server-side at full bit depth. SDR DOM overlays (text, shapes, UI from your HTML) are converted from **sRGB** to **BT.2020** before being layered on top, so colors do not shift.

## [​](https://hyperframes.heygen.com/guides/hdr\#source-media-requirements)  Source Media Requirements

### [​](https://hyperframes.heygen.com/guides/hdr\#hdr-video)  HDR video

Hyperframes recognizes HDR video from its `ffprobe` color space metadata:

| Indicator | Recognized as HDR |
| --- | --- |
| `color_primaries` contains `bt2020` | Yes |
| `color_space` contains `bt2020` | Yes |
| `color_transfer = smpte2084` (PQ) | Yes — PQ |
| `color_transfer = arib-std-b67` (HLG) | Yes — HLG |
| All else (e.g. `bt709`, `smpte170m`) | No — treated as SDR |

A valid HDR source is any MP4 whose stream metadata reports BT.2020 primaries plus PQ or HLG transfer. Hyperframes will detect it automatically:

Terminal

```
ffprobe -v error -show_streams assets/clip.mp4 | grep color
# color_primaries=bt2020
# color_transfer=smpte2084
# color_space=bt2020nc
```

### [​](https://hyperframes.heygen.com/guides/hdr\#hdr-still-images)  HDR still images

Hyperframes supports HDR still images delivered as **16-bit PNGs** tagged with BT.2020 primaries and PQ transfer. Drop them into the composition as a normal `<img>`:

index.html

```
<img class="clip" data-start="0" data-duration="3"
     src="./assets/hdr-photo.png" />
```

When `--hdr` is set, the image is decoded once to 16-bit linear-light RGB and composited natively into the HDR output.

HDR `<img>` decoding is limited to **16-bit PNG**. JPEG, WebP, AVIF, and APNG are not recognized as HDR sources — they load through the normal SDR DOM path. For HDR motion, use a `<video>` element.

### [​](https://hyperframes.heygen.com/guides/hdr\#sdr-sources-mixed-with-hdr)  SDR sources mixed with HDR

You can freely mix SDR and HDR media in the same composition:

- **SDR videos** stay in the DOM screenshot path and get the sRGB → BT.2020 conversion described above
- **HDR videos** are extracted natively at 16-bit and composited underneath the SDR DOM layer
- **SDR images and DOM elements** (text, shapes, gradients, GSAP animations) are converted from sRGB to BT.2020

This is the same pipeline that handles compositions where, for example, an HDR drone clip plays under an SDR lower-third with animated text.

## [​](https://hyperframes.heygen.com/guides/hdr\#output-format-requirements)  Output Format Requirements

| Output format | HDR supported |
| --- | --- |
| `mp4` | Yes — H.265 10-bit BT.2020, HDR10 metadata |
| `mov` | No — falls back to SDR |
| `webm` | No — falls back to SDR |

If you set `--hdr` together with `--format mov` or `--format webm`, Hyperframes logs a message and produces the equivalent SDR render. There is no error — the render still completes — so check the logs (or your verification step) to confirm you got HDR.

## [​](https://hyperframes.heygen.com/guides/hdr\#verifying-hdr-output)  Verifying HDR Output

Use `ffprobe` to confirm both the color tagging and the HDR10 static metadata are present:

Terminal

```
ffprobe -v error -show_streams -select_streams v:0 output.mp4 \
  | grep -E 'codec_name|pix_fmt|color_transfer|color_primaries|color_space'
```

For a PQ HDR10 render you should see:

```
codec_name=hevc
pix_fmt=yuv420p10le
color_space=bt2020nc
color_primaries=bt2020
color_transfer=smpte2084
```

Then check the HDR10 SEI / container boxes:

Terminal

```
ffprobe -v error -show_frames -read_intervals "%+#1" \
  -show_entries frame=side_data_list output.mp4
```

You should see entries for **Mastering display metadata** and **Content light level metadata**. Without them, HDR-aware players will treat the file as SDR BT.2020 and the colors will look washed-out or wrong on an HDR display.For HLG renders the only difference is `color_transfer=arib-std-b67` — the rest of the checks are the same.

## [​](https://hyperframes.heygen.com/guides/hdr\#docker-rendering)  Docker Rendering

`--hdr` is forwarded into the Docker render pipeline, so you can produce HDR10 MP4 output from the containerized renderer:

Terminal

```
npx hyperframes render --hdr --docker --output output.mp4
```

The container runs the same probe → composite → encode pipeline as the local renderer. Verify the output with the same `ffprobe` checks described in [Verifying HDR output](https://hyperframes.heygen.com/guides/hdr#verifying-hdr-output).

Docker HDR rendering currently runs **CPU-side** for the SDR DOM layer (the container falls back to software WebGL because GPU passthrough is not configured by default). Frame capture is therefore slower than local headed Chrome — measure your own composition with `--quiet` off and compare wall-clock times before sizing CI runners. The encoded HDR10 metadata and pixel data are identical to a local render.

## [​](https://hyperframes.heygen.com/guides/hdr\#limitations)  Limitations

- **MP4 only** — `--hdr` with `--format mov` or `--format webm` falls back to SDR
- **HDR images: 16-bit PNG only** — other formats (JPEG, WebP, AVIF, APNG) are not decoded as HDR and fall through the SDR DOM path
- **Player support** — the [`<hyperframes-player>`](https://hyperframes.heygen.com/packages/player) web component plays back the encoded MP4 in the browser and inherits whatever HDR support the host browser provides; it does not implement its own HDR pipeline
- **Headed Chrome HDR DOM capture** — the engine ships a separate WebGPU-based capture path for rendering CSS-animated DOM directly into HDR (`initHdrReadback`, `launchHdrBrowser`). It requires headed Chrome with `--enable-unsafe-webgpu` and is not used by the default render pipeline. See [Engine: HDR](https://hyperframes.heygen.com/packages/engine#hdr-apis) if you are building a custom integration.

## [​](https://hyperframes.heygen.com/guides/hdr\#common-pitfalls)  Common Pitfalls

| Symptom | Likely cause |
| --- | --- |
| Output looks identical to SDR | Source media is SDR — `--hdr` is a no-op without an HDR source. Run `ffprobe` on your inputs |
| Output is “kind of HDR” but tone-mapped wrong on YouTube/QuickTime | Missing HDR10 static metadata on the encoded stream. Verify with the ffprobe snippet above |
| Docker render is much slower than local | Expected — the container falls back to software WebGL for SDR DOM capture. Pixel output is the same |
| Used `--format webm` and got SDR | Expected — HDR output is MP4 only |
| HDR `<img>` looks SDR / washed out | Source is not a 16-bit PNG. Re-export as 16-bit PNG (BT.2020 PQ) or use a `<video>` element instead |

## [​](https://hyperframes.heygen.com/guides/hdr\#next-steps)  Next Steps

## Rendering

Local vs Docker, quality presets, workers

## CLI

Full `render` command reference including `--hdr`

## Engine: HDR APIs

Public HDR utilities exported from `@hyperframes/engine`

## Common Mistakes

Pitfalls that affect render output

[Previous](https://hyperframes.heygen.com/guides/rendering) [PerformanceHow to keep preview playback smooth and diagnose expensive compositions.\\
\\
Next](https://hyperframes.heygen.com/guides/performance)

⌘I

On this page

- [Quickstart](https://hyperframes.heygen.com/guides/hdr#quickstart)
- [How HDR Mode Works](https://hyperframes.heygen.com/guides/hdr#how-hdr-mode-works)
- [Source Media Requirements](https://hyperframes.heygen.com/guides/hdr#source-media-requirements)
- [HDR video](https://hyperframes.heygen.com/guides/hdr#hdr-video)
- [HDR still images](https://hyperframes.heygen.com/guides/hdr#hdr-still-images)
- [SDR sources mixed with HDR](https://hyperframes.heygen.com/guides/hdr#sdr-sources-mixed-with-hdr)
- [Output Format Requirements](https://hyperframes.heygen.com/guides/hdr#output-format-requirements)
- [Verifying HDR Output](https://hyperframes.heygen.com/guides/hdr#verifying-hdr-output)
- [Docker Rendering](https://hyperframes.heygen.com/guides/hdr#docker-rendering)
- [Limitations](https://hyperframes.heygen.com/guides/hdr#limitations)
- [Common Pitfalls](https://hyperframes.heygen.com/guides/hdr#common-pitfalls)
- [Next Steps](https://hyperframes.heygen.com/guides/hdr#next-steps)

Assistant

Responses are generated using AI and may contain mistakes.
