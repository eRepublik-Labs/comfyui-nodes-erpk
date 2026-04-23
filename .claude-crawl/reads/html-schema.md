[Skip to main content](https://hyperframes.heygen.com/reference/html-schema#content-area)

[HyperFrames home page![light logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/light.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=8fff06fe865e474513624008576b71bb)![dark logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/dark.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=5c0e7bb1b0c720593e3f904b47b9e1a3)](https://hyperframes.heygen.com/)

Search...

⌘KAsk AI

Search...

Navigation

Reference

HTML Schema Reference

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

This is the full schema reference for Hyperframes compositions. For a gentler introduction, see [Compositions](https://hyperframes.heygen.com/concepts/compositions) and [Data Attributes](https://hyperframes.heygen.com/concepts/data-attributes).

## [​](https://hyperframes.heygen.com/reference/html-schema\#overview)  Overview

Hyperframes uses HTML as the source of truth for describing a video:

- **HTML clips** = video, image, audio, composition
- **[Data attributes](https://hyperframes.heygen.com/concepts/data-attributes)** = timing, metadata, styling
- **CSS** = positioning and appearance
- **GSAP timeline** = animations and playback sync (see [GSAP Animation](https://hyperframes.heygen.com/guides/gsap-animation))

## [​](https://hyperframes.heygen.com/reference/html-schema\#framework-managed-behavior)  Framework-Managed Behavior

The framework reads data attributes and automatically manages:

- **Primitive clip timeline entries** — reads `data-start`, `data-duration`, and `data-track-index` from clips and adds them to the GSAP timeline
- **Media playback** (play, pause, seek) for `<video>` and `<audio>`
- **Clip lifecycle** — clips are mounted/unmounted based on `data-start` and `data-duration`
- **Timeline synchronization** — keeps media in sync with the GSAP master timeline
- **Media loading** — waits for all media to load before resolving timing

Mounting/unmounting controls **presence**, not appearance. Transitions (fade in, slide in) are animated in scripts.

Do not manually call `video.play()`, `video.pause()`, set `audio.currentTime`, or mount/unmount clips in scripts. The framework owns media playback and clip lifecycle. See [Common Mistakes](https://hyperframes.heygen.com/guides/common-mistakes) for more details.

## [​](https://hyperframes.heygen.com/reference/html-schema\#viewport)  Viewport

Every composition must include `data-width` and `data-height` on the root element:

```
<div id="main" data-composition-id="my-video"
     data-start="0" data-width="1920" data-height="1080">
  <!-- clips -->
</div>
```

Common sizes:

- **Landscape**: `data-width="1920" data-height="1080"`
- **Portrait**: `data-width="1080" data-height="1920"`

## [​](https://hyperframes.heygen.com/reference/html-schema\#all-clip-attributes)  All Clip Attributes

| Attribute | Applies To | Required | Description |
| --- | --- | --- | --- |
| `id` | All | Yes | Unique identifier (e.g., `"el-1"`). Used for relative timing references and CSS targeting. |
| `class="clip"` | Visible elements | Yes | Enables runtime visibility management. Omit for audio-only clips. |
| `data-start` | All | Yes | Start time in seconds (e.g., `"0"`, `"5.5"`), or a clip ID reference for [relative timing](https://hyperframes.heygen.com/reference/html-schema#relative-timing) (e.g., `"intro"`). |
| `data-duration` | video, img, audio | See below | Duration in seconds. **Required** for images. Optional for video/audio (defaults to source duration). Not used on compositions. |
| `data-track-index` | All | Yes | Timeline track number. Controls z-ordering (higher = in front). Clips on the same track cannot overlap. |
| `data-media-start` | video, audio | No | Playback offset / trim point in source file (seconds). Default: `0`. See [Data Attributes](https://hyperframes.heygen.com/concepts/data-attributes). |
| `data-volume` | audio, video | No | Volume level from `0` to `1`. Default: `1`. |
| `data-composition-id` | div | On compositions | Unique composition ID. Must match the key used in `window.__timelines`. |
| `data-composition-src` | div | No | Path to external composition HTML file (for [nested compositions](https://hyperframes.heygen.com/reference/html-schema#composition-clips)). |
| `data-width` | div | On compositions | Composition width in pixels. |
| `data-height` | div | On compositions | Composition height in pixels. |

## [​](https://hyperframes.heygen.com/reference/html-schema\#clip-types)  Clip Types

Video Clips

Video clips embed `<video>` elements with timing and playback attributes.

```
<video
  id="el-1"
  data-start="0"
  data-duration="15"
  data-track-index="0"
  data-media-start="0"
  src="./assets/video.mp4"
></video>
```

**Key behavior:**

- `data-duration` is **optional** — defaults to the remaining duration of the source file from `data-media-start`
- If source media runs out before `data-duration`, the clip shows the last frame (freeze frame)
- `data-media-start` trims the beginning of the source video — `data-media-start="5"` starts playback 5 seconds into the source file
- `data-volume` controls the audio volume of the video — set to `"0"` for silent video
- Do **not** add `class="clip"` to video elements — the framework manages their visibility directly

Do not animate `width`, `height`, `top`, or `left` directly on `<video>` elements with GSAP. This can cause Chrome to stop rendering video frames. Wrap the video in a `<div>` and animate the wrapper instead. See [Common Mistakes](https://hyperframes.heygen.com/guides/common-mistakes).

Image Clips

Image clips display static images with controlled timing.

```
<img
  id="el-2"
  class="clip"
  data-start="5"
  data-duration="4"
  data-track-index="1"
  src="./assets/overlay.png"
/>
```

**Key behavior:**

- `data-duration` is **required** for images (unlike video/audio, there is no source duration to default to)
- `class="clip"` is **required** — this enables the runtime to show/hide the image based on timing
- Supported formats: PNG, JPG, WebP, SVG, GIF (first frame only)
- Position and size with CSS — the image renders at its natural size unless styled otherwise

Audio Clips

Audio clips add sound to the composition without any visual element.

```
<audio
  id="el-4"
  data-start="0"
  data-duration="30"
  data-track-index="2"
  src="./assets/music.mp3"
></audio>
```

**Key behavior:**

- `data-duration` is **optional** — defaults to the remaining duration of the source file from `data-media-start`
- Audio clips are invisible — do not add `class="clip"` (there is nothing to show/hide)
- `data-volume` controls volume — use `"0.5"` for background music at 50% volume
- `data-media-start` trims the beginning of the audio source, just like video
- Multiple audio clips can overlap on different tracks for layered sound design

Composition Clips (Nested)

Composition clips embed one composition inside another, enabling modular, reusable video building blocks.

```
<div
  id="el-5"
  data-composition-id="intro-anim"
  data-composition-src="compositions/intro-anim.html"
  data-start="0"
  data-track-index="3"
></div>
```

**Key behavior:**

- Compositions do **not** use `data-duration` — duration is determined by the composition’s GSAP timeline (`tl.duration()`)
- External compositions are loaded from `data-composition-src` and wrapped in `<template>` tags
- Each nested composition has its own `window.__timelines` entry, registered by its own `<script>` block
- The framework automatically nests sub-timelines — do not manually add them to the parent timeline
- Any composition can be nested inside any other — there is no special “root” type

For more on how compositions work, see [Compositions](https://hyperframes.heygen.com/concepts/compositions).

## [​](https://hyperframes.heygen.com/reference/html-schema\#relative-timing)  Relative Timing

Reference another clip’s ID in `data-start` to mean “start when that clip ends”:

```
<video id="intro" data-start="0" data-duration="10" data-track-index="0" src="..."></video>
<video id="main" data-start="intro" data-duration="20" data-track-index="0" src="..."></video>
```

`main` starts at second 10 (when `intro` ends).**Offsets** let you add gaps or overlaps:

```
<!-- 2-second gap after intro -->
<video id="main" data-start="intro + 2" data-duration="20" data-track-index="0" src="..."></video>

<!-- 0.5-second overlap with intro -->
<video id="main" data-start="intro - 0.5" data-duration="20" data-track-index="0" src="..."></video>
```

For a deeper explanation, see the [relative timing section](https://hyperframes.heygen.com/concepts/data-attributes#relative-timing) in the Data Attributes concept page.

## [​](https://hyperframes.heygen.com/reference/html-schema\#timeline-contract)  Timeline Contract

The framework initializes `window.__timelines = {}` before any scripts run. Every composition must register a GSAP timeline at the key matching its `data-composition-id`:

```
const tl = gsap.timeline({ paused: true });

// Add animations
tl.to("#title", { opacity: 1, duration: 0.5 }, 0);
tl.to("#title", { opacity: 0, duration: 0.5 }, 4.5);

// Register the timeline
window.__timelines["<data-composition-id>"] = tl;
```

### [​](https://hyperframes.heygen.com/reference/html-schema\#rules)  Rules

- Every composition needs a `<script>` block that creates and registers its timeline
- All timelines must start paused (`{ paused: true }`)
- The framework auto-nests sub-timelines into the parent — do **not** manually add them
- Duration comes from `tl.duration()` — do **not** add `data-duration` on composition elements
- Timelines must be finite (no infinite loops or repeats)
- The timeline ID must exactly match the `data-composition-id` attribute on the root element

For a complete guide to working with GSAP timelines, see [GSAP Animation](https://hyperframes.heygen.com/guides/gsap-animation).

## [​](https://hyperframes.heygen.com/reference/html-schema\#caption-discoverability)  Caption Discoverability

For caption compositions, add these attributes to the root node so the framework can identify and special-case caption rendering:

```
<div
  data-composition-id="captions"
  data-timeline-role="captions"
  data-caption-root="true"
  ...
>
```

## [​](https://hyperframes.heygen.com/reference/html-schema\#output-checklist)  Output Checklist

Before rendering, verify your composition meets these requirements:

- Every composition has `data-width` and `data-height` on the root element
- Each reusable composition is in its own HTML file
- External compositions are loaded via `data-composition-src`
- Each external composition file uses a `<template>` wrapper
- All GSAP timelines are registered in `window.__timelines` with the correct ID
- Timed visible elements (images, divs) have `class="clip"`
- Video elements do **not** have `class="clip"` (framework manages them directly)
- All `data-start` references point to existing clip IDs
- Run `npx hyperframes lint` to catch structural issues automatically

[ContributingHow to contribute to Hyperframes.\\
\\
Next](https://hyperframes.heygen.com/contributing)

⌘I

On this page

- [Overview](https://hyperframes.heygen.com/reference/html-schema#overview)
- [Framework-Managed Behavior](https://hyperframes.heygen.com/reference/html-schema#framework-managed-behavior)
- [Viewport](https://hyperframes.heygen.com/reference/html-schema#viewport)
- [All Clip Attributes](https://hyperframes.heygen.com/reference/html-schema#all-clip-attributes)
- [Clip Types](https://hyperframes.heygen.com/reference/html-schema#clip-types)
- [Relative Timing](https://hyperframes.heygen.com/reference/html-schema#relative-timing)
- [Timeline Contract](https://hyperframes.heygen.com/reference/html-schema#timeline-contract)
- [Rules](https://hyperframes.heygen.com/reference/html-schema#rules)
- [Caption Discoverability](https://hyperframes.heygen.com/reference/html-schema#caption-discoverability)
- [Output Checklist](https://hyperframes.heygen.com/reference/html-schema#output-checklist)

Assistant

Responses are generated using AI and may contain mistakes.
