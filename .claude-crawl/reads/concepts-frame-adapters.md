[Skip to main content](https://hyperframes.heygen.com/concepts/frame-adapters#content-area)

[HyperFrames home page![light logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/light.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=8fff06fe865e474513624008576b71bb)![dark logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/dark.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=5c0e7bb1b0c720593e3f904b47b9e1a3)](https://hyperframes.heygen.com/)

Search...

⌘KAsk AI

Search...

Navigation

Concepts

Frame Adapters

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

The Frame Adapter pattern is how Hyperframes supports multiple animation runtimes. The core question every adapter answers:

> What should the screen look like at frame N?

If a runtime can answer that, it can plug into Hyperframes.

The Adapter API is currently at **v0** (experimental). Breaking changes are possible until v1. The core contract (seek-by-frame, deterministic output) is stable, but method signatures may evolve.

## [​](https://hyperframes.heygen.com/concepts/frame-adapters\#how-it-works)  How It Works

The host application (the [engine](https://hyperframes.heygen.com/packages/engine) or [producer](https://hyperframes.heygen.com/packages/producer)) drives rendering by calling adapter methods in a strict sequence. The adapter never controls its own clock — it only responds to seek commands.

## [​](https://hyperframes.heygen.com/concepts/frame-adapters\#adapter-api-v0)  Adapter API (v0)

adapters/types.ts

```
type FrameAdapterContext = {
  compositionId: string;
  fps: number;
  width: number;
  height: number;
  rootElement?: HTMLElement;
};

type FrameAdapter = {
  id: string;
  init?: (ctx: FrameAdapterContext) => Promise<void> | void;
  getDurationFrames: () => number;
  seekFrame: (frame: number) => Promise<void> | void;
  destroy?: () => Promise<void> | void;
};
```

## [​](https://hyperframes.heygen.com/concepts/frame-adapters\#required-semantics)  Required Semantics

- `getDurationFrames()` must return a finite integer >= 0
- `seekFrame(frame)` must support arbitrary seek order (forward, backward, random)
- `seekFrame(frame)` must be idempotent for the same input frame
- `seekFrame(frame)` must clamp internal time to the adapter’s range
- Adapters should be paused/seek-driven, not clock-driven

## [​](https://hyperframes.heygen.com/concepts/frame-adapters\#host-orchestration)  Host Orchestration

The host normalizes frames before calling the adapter:

engine/render-loop.ts

```
normalizedFrame = clamp(Math.floor(frame), 0, durationFrames);
```

A typical render loop:

engine/render-loop.ts

```
await adapter.init?.({ compositionId, fps, width, height, rootElement });
const durationFrames = adapter.getDurationFrames();

for (let frame = 0; frame <= durationFrames; frame += 1) {
  await adapter.seekFrame(frame);
  // capture pixel buffer for this frame
}

await adapter.destroy?.();
```

## [​](https://hyperframes.heygen.com/concepts/frame-adapters\#determinism-contract)  Determinism Contract

These rules are non-negotiable for any adapter. They are the foundation of Hyperframes’ [deterministic rendering](https://hyperframes.heygen.com/concepts/determinism) guarantee.

- Canonical clock: `t = frame / fps`
- No wall-clock dependencies (`Date.now`, drift-dependent logic)
- No unseeded randomness
- No render-time network fetches
- Fixed output params (`fps`, `width`, `height`)
- Finite duration only
- Deterministic frame quantization before seek

## [​](https://hyperframes.heygen.com/concepts/frame-adapters\#supported-runtimes)  Supported Runtimes

First-party adapters:

| Runtime | Seek Method | Status |
| --- | --- | --- |
| [GSAP](https://hyperframes.heygen.com/guides/gsap-animation) | `timeline.seek(frame / fps)` | Available |
| CSS/WAAPI | `animation.currentTime` | Planned |
| Lottie | Set animation frame/progress | Planned |
| Three.js/WebGL | Compute deterministic scene state | Planned |
| SVG/Anime | Implement seek + duration contract | Planned |

Community adapters are welcome — if it can seek by frame, it belongs in Hyperframes.

## [​](https://hyperframes.heygen.com/concepts/frame-adapters\#conformance-tests)  Conformance Tests

Every adapter should pass these minimum tests:

1. **Repeatability** — seek same frame twice, get identical output
2. **Random seek** — seek order `[90, 10, 50, 10]` produces deterministic results
3. **Bounds** — negative and overflow frame values do not break
4. **Duration** — returned duration is a finite integer
5. **Cleanup** — no leaked timers/listeners after `destroy`

## [​](https://hyperframes.heygen.com/concepts/frame-adapters\#next-steps)  Next Steps

## Deterministic Rendering

Understand the determinism guarantees adapters must uphold

## GSAP Animation

See the first-party GSAP adapter in action

## @hyperframes/engine

The capture engine that drives adapters during rendering

## Contributing

Build and contribute your own adapter

[Previous](https://hyperframes.heygen.com/concepts/data-attributes) [Deterministic RenderingSame input, identical output. Every time.\\
\\
Next](https://hyperframes.heygen.com/concepts/determinism)

⌘I

On this page

- [How It Works](https://hyperframes.heygen.com/concepts/frame-adapters#how-it-works)
- [Adapter API (v0)](https://hyperframes.heygen.com/concepts/frame-adapters#adapter-api-v0)
- [Required Semantics](https://hyperframes.heygen.com/concepts/frame-adapters#required-semantics)
- [Host Orchestration](https://hyperframes.heygen.com/concepts/frame-adapters#host-orchestration)
- [Determinism Contract](https://hyperframes.heygen.com/concepts/frame-adapters#determinism-contract)
- [Supported Runtimes](https://hyperframes.heygen.com/concepts/frame-adapters#supported-runtimes)
- [Conformance Tests](https://hyperframes.heygen.com/concepts/frame-adapters#conformance-tests)
- [Next Steps](https://hyperframes.heygen.com/concepts/frame-adapters#next-steps)

Assistant

Responses are generated using AI and may contain mistakes.
