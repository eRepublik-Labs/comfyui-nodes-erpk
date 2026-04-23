[Skip to main content](https://hyperframes.heygen.com/guides/common-mistakes#content-area)

[HyperFrames home page![light logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/light.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=8fff06fe865e474513624008576b71bb)![dark logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/dark.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=5c0e7bb1b0c720593e3f904b47b9e1a3)](https://hyperframes.heygen.com/)

Search...

Ctrl KAsk AI

Search...

Navigation

Guides

Common Mistakes

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

These are mistakes that cannot be caught by the linter. For automated checks, run `npx hyperframes lint` (see [CLI](https://hyperframes.heygen.com/packages/cli#lint)).

The first two mistakes — animating video element dimensions and controlling media playback in scripts — are the most common causes of broken compositions. If your video looks wrong, check these first.

Animating video element dimensions

**Symptom:** Video frames stop updating, or browser performance drops severely.**Cause:** GSAP animating `width`, `height`, `top`, `left` directly on a `<video>` element can cause the browser to stop rendering frames.**Before (broken):**

index.html

```
// Animating the video element directly — causes frame rendering to stop
tl.to("#el-video", { width: 500, height: 280, top: 700, left: 1400 }, 26);
```

**After (fixed):**

index.html

```
<!-- Wrap the video in a div and animate the wrapper -->
<div id="pip-wrapper" style="position: absolute; width: 1920px; height: 1080px;">
  <video id="el-video" data-start="0" data-track-index="0"
         src="./assets/video.mp4" style="width: 100%; height: 100%;"></video>
</div>
```

index.html

```
// Animate the wrapper — the video fills it at 100%
tl.to("#pip-wrapper", { width: 500, height: 280, top: 700, left: 1400 }, 26);
```

Use a non-timed wrapper `<div>` for visual effects like picture-in-picture. Animate the wrapper; let the video fill it via CSS.

Controlling media playback in scripts

**Symptom:** Audio/video playback is out of sync, or plays when it should not.**Cause:** Calling `video.play()`, `video.pause()`, or setting `audio.currentTime` in your scripts. The [framework owns all media playback](https://hyperframes.heygen.com/reference/html-schema#framework-managed-behavior).**Before (broken):**

index.html

```
// Conflicts with framework media sync
document.getElementById("el-video").play();
document.getElementById("el-audio").currentTime = 5;
```

**After (fixed):**

index.html

```
// Don't control media playback at all. The framework handles it.
// Use GSAP for visual animations only:
tl.to("#el-video", { opacity: 1, duration: 0.5 }, 0);
```

The framework reads [`data-start`](https://hyperframes.heygen.com/concepts/data-attributes#timing-attributes), [`data-media-start`](https://hyperframes.heygen.com/concepts/data-attributes#media-attributes), and [`data-volume`](https://hyperframes.heygen.com/concepts/data-attributes#media-attributes) to control when and how media plays. See [Compositions: Two Layers](https://hyperframes.heygen.com/concepts/compositions#two-layers-primitives-and-scripts) for the separation between HTML primitives and scripts.

Composition duration shorter than video

**Symptom:** Video plays for a few seconds then stops. Timeline shows 8-10 seconds even though the video is minutes long.**Cause:** The composition duration equals the [GSAP timeline duration](https://hyperframes.heygen.com/guides/gsap-animation#timeline-duration-and-composition-duration), not `data-duration` on the video. If your last GSAP animation ends at 8 seconds, the composition is 8 seconds long — regardless of how long the video source is.**Before (broken):**

index.html

```
// Timeline is only 7.8s long — video cuts off after 7.8 seconds
tl.to("#lower-third", { left: -640, duration: 0.6 }, 7.2);
```

**After (fixed):**

index.html

```
tl.to("#lower-third", { left: -640, duration: 0.6 }, 7.2);

// Extend the timeline to 283 seconds to match the video length
tl.set({}, {}, 283);
```

`tl.set({}, {}, TIME)` adds a zero-duration tween at the specified time, extending the timeline without affecting any elements.

A quick check: run `npx hyperframes compositions` to see the resolved duration of each composition. If it is shorter than expected, your timeline needs extending.

Missing class='clip' on timed elements

**Symptom:** Elements are always visible, ignoring their `data-start` and `data-duration` timing.**Cause:** The [`class="clip"`](https://hyperframes.heygen.com/concepts/data-attributes#element-visibility) attribute tells the runtime to manage the element’s visibility lifecycle. Without it, the element is always rendered.**Before (broken):**

index.html

```
<!-- Missing class="clip" — this element is always visible -->
<h1 id="title" data-start="2" data-duration="5" data-track-index="0">
  Hello World
</h1>
```

**After (fixed):**

index.html

```
<!-- With class="clip", the runtime shows this only from 2s to 7s -->
<h1 id="title" class="clip" data-start="2" data-duration="5" data-track-index="0">
  Hello World
</h1>
```

The linter catches this one: `npx hyperframes lint` will flag timed elements missing `class="clip"`.

Oversized source images

**Symptom:** Preview stutters during scenes with images on screen. Render is slower than expected.**Cause:** Source images at much higher resolution than the canvas. Chrome decodes images to raw RGBA bitmaps before displaying them, and bitmap size is `width × height × 4` bytes — independent of file size on disk. A 7000×5000 JPEG is 140MB decoded, even if the file is only 2MB.Displaying such an image in a 384×1080 region wastes memory and forces the compositor to resample a huge texture every frame.**Before (bloated):**

index.html

```
<!-- 7000x5000 source, ~140MB decoded -->
<img class="clip" data-start="0" data-duration="3"
     src="./assets/hero-scene.jpg" />
```

**After (sized to the canvas):**

Terminal

```
# Resize a batch of images to fit within 3840x3840, preserving aspect ratio
mkdir -p assets/resized
mogrify -path assets/resized -resize 3840x3840\> assets/*.jpg
```

index.html

```
<!-- ~3840x2560 source, ~40MB decoded -->
<img class="clip" data-start="0" data-duration="3"
     src="./assets/resized/hero-scene.jpg" />
```

**Rule of thumb:** source images at most 2x the canvas dimensions. For a 1920×1080 composition, 3840×2160 is already plenty. See [Performance: Image sizing](https://hyperframes.heygen.com/guides/performance#image-sizing).

Heavy backdrop-filter stacks

**Symptom:** Specific scenes drop to 5-10fps in preview. The composition is fine elsewhere.**Cause:**`backdrop-filter: blur()` on large elements, especially stacked at high radii. Each blur layer forces the compositor to sample pixels behind the element, run a blur kernel, and composite the result. Stacked layers multiply the cost.**Before (expensive):**

```
/* 8 layers per side = 16 blur passes every frame */
.pb-1 { backdrop-filter: blur(1px); }
.pb-2 { backdrop-filter: blur(2px); }
.pb-3 { backdrop-filter: blur(4px); }
.pb-4 { backdrop-filter: blur(8px); }
.pb-5 { backdrop-filter: blur(16px); }
.pb-6 { backdrop-filter: blur(32px); }
.pb-7 { backdrop-filter: blur(64px); }
.pb-8 { backdrop-filter: blur(128px); }
```

**After (3 tuned layers):**

```
/* Fewer passes with hand-picked radii — visually similar, much cheaper */
.pb-1 { backdrop-filter: blur(4px); }
.pb-2 { backdrop-filter: blur(16px); }
.pb-3 { backdrop-filter: blur(48px); }
```

**Guidelines:**

- Keep stacked `backdrop-filter` layers to 2-3 per region
- Avoid radii above 64px over large areas — the biggest radii dominate the total cost
- For a static blur effect, pre-render it into a PNG once and overlay with a regular `<img>`

See [Performance: backdrop-filter: blur()](https://hyperframes.heygen.com/guides/performance#backdrop-filter-blur) for the full breakdown.

Expected HDR output but got SDR

**Symptom:** Rendered with `--hdr`, but the output looks the same as SDR or `ffprobe` reports `color_transfer=bt709`.**Cause:**`--hdr` is a _detection_ flag, not a _force_ flag. Hyperframes only switches to HDR encoding when a source `<video>` or `<img>` is tagged with BT.2020 / PQ / HLG color metadata. Two common reasons HDR is not engaged:

1. **All sources are SDR.**`--hdr` is a no-op on SDR-only compositions. Verify with `ffprobe`:




Terminal





















```
ffprobe -v error -show_streams source.mp4 | grep color_transfer
# Want: smpte2084 (PQ) or arib-std-b67 (HLG)
# SDR:  bt709, smpte170m, bt470bg, etc.
```

2. **Wrong output format.** HDR output requires MP4. `--format mov` and `--format webm` fall back to SDR — Hyperframes logs a warning when this happens.

`--docker` works the same as local rendering — `--hdr` is forwarded into the container and produces the same HDR10 MP4 output (slower, since the container falls back to software WebGL for SDR DOM capture).See [HDR Rendering](https://hyperframes.heygen.com/guides/hdr) for the full source requirements and verification steps.

Timeline key doesn't match data-composition-id

**Symptom:** Animations don’t play. The composition appears static.**Cause:** The key used in `window.__timelines` must exactly match the [`data-composition-id`](https://hyperframes.heygen.com/concepts/data-attributes#composition-attributes) attribute on the composition root element.**Before (broken):**

index.html

```
// Mismatch: HTML says "my-video", script registers "root"
// <div data-composition-id="my-video" ...>
window.__timelines["root"] = tl;
```

**After (fixed):**

index.html

```
// Key matches the data-composition-id attribute
// <div data-composition-id="my-video" ...>
window.__timelines["my-video"] = tl;
```

## [​](https://hyperframes.heygen.com/guides/common-mistakes\#debugging-checklist)  Debugging Checklist

When something does not work, check in this order:

1. **Run the linter:**`npx hyperframes lint` — catches most structural issues
2. **Timeline registered?** Is `window.__timelines["<id>"]` set? Does the key match [`data-composition-id`](https://hyperframes.heygen.com/concepts/data-attributes#composition-attributes)?
3. **GSAP-only animations?** Only animate visual properties (opacity, transform, color) — see [GSAP Animation](https://hyperframes.heygen.com/guides/gsap-animation#key-rules)
4. **Timeline long enough?** Add `tl.set({}, {}, DURATION)` at the end — see [Timeline Duration](https://hyperframes.heygen.com/guides/gsap-animation#timeline-duration-and-composition-duration)
5. **Console errors?** Open browser console — runtime errors show as `[Browser:ERROR]`
6. **Still stuck?** See [Troubleshooting](https://hyperframes.heygen.com/guides/troubleshooting) for environment and rendering issues

## [​](https://hyperframes.heygen.com/guides/common-mistakes\#next-steps)  Next Steps

[**Troubleshooting** \\
\\
Fix environment and rendering issues](https://hyperframes.heygen.com/guides/troubleshooting)

[**GSAP Animation** \\
\\
Review animation rules and patterns](https://hyperframes.heygen.com/guides/gsap-animation)

[**HTML Schema Reference** \\
\\
Full attribute reference and checklist](https://hyperframes.heygen.com/reference/html-schema)

[**Data Attributes** \\
\\
Timing, media, and composition attributes](https://hyperframes.heygen.com/concepts/data-attributes)

[Previous](https://hyperframes.heygen.com/guides/performance) [TroubleshootingSolutions for common Hyperframes issues.\\
\\
Next](https://hyperframes.heygen.com/guides/troubleshooting)

Ctrl+I

On this page

- [Debugging Checklist](https://hyperframes.heygen.com/guides/common-mistakes#debugging-checklist)
- [Next Steps](https://hyperframes.heygen.com/guides/common-mistakes#next-steps)

Assistant

Responses are generated using AI and may contain mistakes.
