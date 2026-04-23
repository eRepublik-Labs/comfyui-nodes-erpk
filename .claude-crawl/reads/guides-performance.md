[Skip to main content](https://hyperframes.heygen.com/guides/performance#content-area)

[HyperFrames home page![light logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/light.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=8fff06fe865e474513624008576b71bb)![dark logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/dark.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=5c0e7bb1b0c720593e3f904b47b9e1a3)](https://hyperframes.heygen.com/)

Search...

⌘KAsk AI

Search...

Navigation

Guides

Performance

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

Preview plays your composition in real time, so any frame that takes longer than 33ms (at 30fps) shows up as stutter. This page covers the patterns that blow that budget and how to spot them.

## [​](https://hyperframes.heygen.com/guides/performance\#preview-vs-render)  Preview vs. render

Render captures frames one at a time and stitches them into a video. Slow frames make the render take longer, but you never see the pauses — you watch the finished mp4.Preview does the same work in real time. If a frame takes 200ms to paint, you see a 200ms freeze.This is why “render looks fine, preview stutters” is expected for paint-heavy compositions. It doesn’t mean preview is broken — it means individual frames are too expensive for real-time playback.

## [​](https://hyperframes.heygen.com/guides/performance\#expensive-css-patterns)  Expensive CSS patterns

These are the patterns that most often cause preview to drop below 30fps.

### [​](https://hyperframes.heygen.com/guides/performance\#backdrop-filter-blur)  backdrop-filter: blur()

Each `backdrop-filter: blur(radius)` sampled over a large area forces the compositor to read pixels from behind the element, run a blur kernel across them, and composite the result. Cost scales with both the blurred area and the radius.Stacked blur layers multiply the cost. Eight layers at progressively larger radii (1, 2, 4, 8, 16, 32, 64, 128px) will happily take 200ms per frame over a 1920x1080 region on mid-tier GPUs.**What to do:**

- Keep stacked layers to 2-3 maximum, with manually tuned radii
- Avoid `blur(128px)` or `blur(64px)` over large areas — the biggest radii dominate the cost
- For a static blur, render it once into a PNG and use a regular `<img>` overlay

### [​](https://hyperframes.heygen.com/guides/performance\#filter-blur-and-filter-drop-shadow)  filter: blur() and filter: drop-shadow()

Same story as `backdrop-filter` but applied to the element itself rather than behind it. Fine on small elements, expensive on large ones.

### [​](https://hyperframes.heygen.com/guides/performance\#shadows-on-many-elements)  Shadows on many elements

`box-shadow` and `text-shadow` on a few elements are fine. On dozens of elements that also animate, the compositor re-rasterizes each shadowed layer on every frame.

### [​](https://hyperframes.heygen.com/guides/performance\#large-gradients-with-mask-image)  Large gradients with mask-image

Combined with `backdrop-filter`, `mask-image` can force additional compositor passes. If you have both on the same element, consider whether you need both.

## [​](https://hyperframes.heygen.com/guides/performance\#image-sizing)  Image sizing

Image source resolution matters more than file size. Chrome decodes JPEGs and PNGs to raw RGBA bitmaps before displaying them — a decoded bitmap is:

```
bitmap_bytes = width × height × 4
```

A 7000×5000 source image is 140MB decoded, regardless of whether the JPEG on disk is 2MB or 5MB.**Rule of thumb:** resize source images to at most 2x the canvas dimensions. For a 1920x1080 canvas, 3840x2160 source images are already overkill. Anything above that is paying for memory and texture-upload cost that never shows on screen.

Terminal

```
# ImageMagick one-liner to downsize a directory of images
mogrify -path resized -resize 3840x3840\> *.jpg
```

## [​](https://hyperframes.heygen.com/guides/performance\#measuring-a-slow-composition)  Measuring a slow composition

Don’t guess — measure. Chrome DevTools has everything you need.

1

[Navigate to header](https://hyperframes.heygen.com/guides/performance#)

Run preview

Start the preview server and open it in Chrome:

Terminal

```
npx hyperframes preview
```

2

[Navigate to header](https://hyperframes.heygen.com/guides/performance#)

Open DevTools → Performance

`Cmd+Option+I` (macOS) or `Ctrl+Shift+I` (Linux/Windows), then switch to the **Performance** tab.

3

[Navigate to header](https://hyperframes.heygen.com/guides/performance#)

Record during playback

Hit the record button, click play in the preview, let it run 3-5 seconds through the jank-prone scene, then stop recording.

4

[Navigate to header](https://hyperframes.heygen.com/guides/performance#)

Read the main thread track

Look for long tasks (red-flagged in the timeline). Expand the tallest bars and check what Chrome labels them:

- **Composite Layers / Paint** with a large duration = compositor cost (backdrop-filter, shadows, large textures)
- **Decode Image** = image decode on first paint (rare in Chrome 131+, images decode off-thread by default)
- **Layout / Recalculate Style** = layout thrashing from script
- **Script** = JS work (rare for compositions, check author scripts)

Once you know which category dominates, you know what to change.

A composition that runs at 60fps in isolation but stutters only during specific scenes is usually a composite-cost problem. Check which layers become visible during those scenes.

## [​](https://hyperframes.heygen.com/guides/performance\#when-preview-is-unavoidable-slow)  When preview is unavoidable slow

Some compositions are legitimately too expensive for real-time playback. If you’ve reduced what you can and preview still stutters, render-to-mp4 and watch the output is a fine workflow — render is still accurate.

Terminal

```
npx hyperframes render --quality draft --output preview.mp4
```

Draft quality renders fast and is visually close to the final render for everything except encoder-level detail.

## [​](https://hyperframes.heygen.com/guides/performance\#next-steps)  Next Steps

## Troubleshooting

Environment, tooling, and rendering issues

## Common Mistakes

Composition pitfalls that break rendering

## Rendering

Rendering modes, options, and flags

## CLI Reference

Full list of CLI commands

[Previous](https://hyperframes.heygen.com/guides/hdr) [Common MistakesPitfalls that break Hyperframes compositions.\\
\\
Next](https://hyperframes.heygen.com/guides/common-mistakes)

⌘I

On this page

- [Preview vs. render](https://hyperframes.heygen.com/guides/performance#preview-vs-render)
- [Expensive CSS patterns](https://hyperframes.heygen.com/guides/performance#expensive-css-patterns)
- [backdrop-filter: blur()](https://hyperframes.heygen.com/guides/performance#backdrop-filter-blur)
- [filter: blur() and filter: drop-shadow()](https://hyperframes.heygen.com/guides/performance#filter-blur-and-filter-drop-shadow)
- [Shadows on many elements](https://hyperframes.heygen.com/guides/performance#shadows-on-many-elements)
- [Large gradients with mask-image](https://hyperframes.heygen.com/guides/performance#large-gradients-with-mask-image)
- [Image sizing](https://hyperframes.heygen.com/guides/performance#image-sizing)
- [Measuring a slow composition](https://hyperframes.heygen.com/guides/performance#measuring-a-slow-composition)
- [When preview is unavoidable slow](https://hyperframes.heygen.com/guides/performance#when-preview-is-unavoidable-slow)
- [Next Steps](https://hyperframes.heygen.com/guides/performance#next-steps)

Assistant

Responses are generated using AI and may contain mistakes.
