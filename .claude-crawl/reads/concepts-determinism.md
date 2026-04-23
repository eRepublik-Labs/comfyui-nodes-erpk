[Skip to main content](https://hyperframes.heygen.com/concepts/determinism#content-area)

[HyperFrames home page![light logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/light.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=8fff06fe865e474513624008576b71bb)![dark logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/dark.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=5c0e7bb1b0c720593e3f904b47b9e1a3)](https://hyperframes.heygen.com/)

Search...

⌘KAsk AI

Search...

Navigation

Concepts

Deterministic Rendering

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

Hyperframes is built around a core guarantee: **the same [composition](https://hyperframes.heygen.com/concepts/compositions) always produces the same video**. This is what makes automated pipelines, CI testing, and AI-driven workflows reliable.

## [​](https://hyperframes.heygen.com/concepts/determinism\#how-it-works)  How It Works

The rendering pipeline is frame-by-frame and seek-driven. No realtime playback is involved — every frame is independently seeked and captured.

1

[Navigate to header](https://hyperframes.heygen.com/concepts/determinism#)

Frame clock

The [engine](https://hyperframes.heygen.com/packages/engine) computes the time for each frame using integer math: `time = floor(frame) / fps`. There is no wall-clock dependency — rendering is entirely decoupled from real time.

2

[Navigate to header](https://hyperframes.heygen.com/concepts/determinism#)

Seek

The [frame adapter](https://hyperframes.heygen.com/concepts/frame-adapters) receives a `seekFrame(frame)` call and deterministically positions all animations, DOM state, and canvas content to the exact frame. The adapter’s `renderSeek` pauses all [GSAP](https://hyperframes.heygen.com/guides/gsap-animation) timelines and seeks them to the computed time.

3

[Navigate to header](https://hyperframes.heygen.com/concepts/determinism#)

Capture

Chrome’s `HeadlessExperimental.beginFrame` API captures the pixel buffer for the current frame. This is a single, atomic operation — no partial paints or race conditions.

4

[Navigate to header](https://hyperframes.heygen.com/concepts/determinism#)

Encode

FFmpeg encodes the captured frames into the final MP4 video. Audio tracks from `<audio>` and `<video>` elements are mixed in during this stage.

## [​](https://hyperframes.heygen.com/concepts/determinism\#what-makes-it-deterministic)  What Makes It Deterministic

- **No wall-clock dependencies** — rendering does not use `Date.now()`, `requestAnimationFrame`, or system timers
- **No unseeded randomness** — `Math.random()` without a seed breaks determinism
- **No render-time network fetches** — all assets must be loaded before rendering starts
- **Fixed output parameters** — `fps`, `width`, and `height` are locked before the first frame
- **Finite duration** — every [composition](https://hyperframes.heygen.com/concepts/compositions) has a known, finite length

These same rules apply to every [frame adapter](https://hyperframes.heygen.com/concepts/frame-adapters). If you are building a custom adapter, you must follow the [determinism contract](https://hyperframes.heygen.com/concepts/frame-adapters#determinism-contract).

## [​](https://hyperframes.heygen.com/concepts/determinism\#docker-mode)  Docker Mode

For maximum reproducibility, render in Docker:

```
npx hyperframes render --docker --output output.mp4
```

Docker mode uses an exact Chrome version and font set, ensuring:

- Same Chromium rendering engine across all platforms
- Same system fonts (no platform-specific font substitution)
- Same FFmpeg encoder version

See the [Rendering guide](https://hyperframes.heygen.com/guides/rendering) for all rendering options.

## [​](https://hyperframes.heygen.com/concepts/determinism\#preview-vs-render-parity)  Preview vs. Render Parity

The browser preview and the rendered MP4 should match. Hyperframes achieves this through:

- **One runtime** — the same `hyperframe.runtime` drives both preview and render
- **Producer-canonical behavior** — the [producer’s](https://hyperframes.heygen.com/packages/producer) seek semantics are the source of truth
- **Readiness gates** — `__playerReady` and `__renderReady` ensure the [composition](https://hyperframes.heygen.com/concepts/compositions) is fully loaded before any frame is captured

Parity here means **visual fidelity** — every frame looks the same. It does _not_ mean performance parity. Preview plays in real time in a browser, so frame-rate limits are bound by your hardware. Render is seek-driven and frame-at-a-time, so it never drops frames regardless of per-frame cost. A composition can stutter in preview and render perfectly. See [Performance](https://hyperframes.heygen.com/guides/performance) for why.

Local rendering (without Docker) may show slight differences due to platform-specific font rendering and Chrome version. Use Docker mode when exact reproducibility matters.

## [​](https://hyperframes.heygen.com/concepts/determinism\#for-adapter-authors)  For Adapter Authors

If you are building a [frame adapter](https://hyperframes.heygen.com/concepts/frame-adapters), your adapter must follow the determinism contract:

- `seekFrame(frame)` must be idempotent — same frame, same result
- No side effects that depend on call order (must handle random access)
- No async operations that resolve after the frame is “committed”
- Clean lifecycle: `init` -\> `seekFrame` (N times) -> `destroy`

## [​](https://hyperframes.heygen.com/concepts/determinism\#next-steps)  Next Steps

## Frame Adapters

Build adapters that uphold the determinism contract

## Rendering

Render to MP4 locally or in Docker

## @hyperframes/producer

The full rendering pipeline that orchestrates deterministic output

## Common Mistakes

Pitfalls that break determinism and how to avoid them

[Previous](https://hyperframes.heygen.com/concepts/frame-adapters) [Website to VideoCapture any website and turn it into a production video with a single prompt.\\
\\
Next](https://hyperframes.heygen.com/guides/website-to-video)

⌘I

On this page

- [How It Works](https://hyperframes.heygen.com/concepts/determinism#how-it-works)
- [What Makes It Deterministic](https://hyperframes.heygen.com/concepts/determinism#what-makes-it-deterministic)
- [Docker Mode](https://hyperframes.heygen.com/concepts/determinism#docker-mode)
- [Preview vs. Render Parity](https://hyperframes.heygen.com/concepts/determinism#preview-vs-render-parity)
- [For Adapter Authors](https://hyperframes.heygen.com/concepts/determinism#for-adapter-authors)
- [Next Steps](https://hyperframes.heygen.com/concepts/determinism#next-steps)

Assistant

Responses are generated using AI and may contain mistakes.
