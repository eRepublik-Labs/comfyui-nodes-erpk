[Skip to main content](https://hyperframes.heygen.com/introduction#content-area)

[HyperFrames home page![light logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/light.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=8fff06fe865e474513624008576b71bb)![dark logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/dark.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=5c0e7bb1b0c720593e3f904b47b9e1a3)](https://hyperframes.heygen.com/)

Search...

Ctrl KAsk AI

Search...

Navigation

Getting Started

Introduction

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

Hyperframes is an open-source framework that turns HTML into deterministic, frame-by-frame rendered video — so you can define a video the same way you build a web page.

## [​](https://hyperframes.heygen.com/introduction\#see-it-in-action)  See It in Action

Here is a video defined entirely as HTML:

```
<div id="root" data-composition-id="demo"
     data-start="0" data-width="1920" data-height="1080">

  <video id="clip-1" data-start="0" data-duration="5"
         data-track-index="0" src="intro.mp4" muted playsinline></video>

  <h1 id="title" class="clip"
      data-start="1" data-duration="4" data-track-index="1"
      style="font-size: 72px; color: white;">
    Welcome to Hyperframes
  </h1>

  <audio id="bg-music" data-start="0" data-duration="5"
         data-track-index="2" data-volume="0.5" src="music.wav"></audio>
</div>
```

Run `npx hyperframes render --output demo.mp4` and this produces an MP4 with deterministic, frame-by-frame capture. Same input, identical output, every time. No timeline editor. No proprietary format. Just HTML.

[**Browse the Catalog** \\
\\
50+ ready-to-use blocks and components — social overlays, shader transitions, data visualizations, and cinematic effects. Install any of them with one command.](https://hyperframes.heygen.com/catalog/blocks/data-chart)

[**Quick Start** \\
\\
Go from zero to rendered video in under 5 minutes.](https://hyperframes.heygen.com/quickstart)

## [​](https://hyperframes.heygen.com/introduction\#why-hyperframes)  Why Hyperframes?

- For developers

- For AI agents

- For automated pipelines


**You already know the stack.** Compositions are HTML files with data attributes. Animations use GSAP, Lottie, CSS, or any runtime that can seek to a given frame. There is no custom DSL, no proprietary component system, and no React requirement. If you can build a web page, you can build a video.

**Agents already speak HTML.** Most video tools require complex APIs or drag-and-drop interfaces that agents cannot operate. Hyperframes compositions are plain HTML documents — the format LLMs are best at generating. The CLI is non-interactive by default — all inputs via flags, plain text output, fail-fast on errors — so agents can drive every command without prompts or parsing.

**Determinism by design.** The rendering pipeline is seek-driven with no wall-clock dependencies. `frame = floor(time * fps)` — every frame is independently captured via Chrome’s `beginFrame` API and encoded with FFmpeg. Same input always produces identical output, making CI testing and batch rendering reliable.

Hyperframes was designed from the ground up for AI agent integration. Compositions are plain HTML that any LLM can generate. The CLI is non-interactive by default — flag-driven with plain text output — so agents can scaffold, render, and lint without interactive prompts. Add `--human-friendly` for the interactive terminal UI. See [CLI](https://hyperframes.heygen.com/packages/cli) for details.

## [​](https://hyperframes.heygen.com/introduction\#how-it-works)  How It Works

1

[Navigate to header](https://hyperframes.heygen.com/introduction#)

Write HTML

Define your video as an HTML document. Each element gets data attributes for timing (`data-start`, `data-duration`) and layout (`data-track-index`). Add animations with GSAP, Lottie, CSS transitions, or any seekable runtime via the Frame Adapter pattern.

2

[Navigate to header](https://hyperframes.heygen.com/introduction#)

Preview in the browser

Run `npx hyperframes preview` to open a live preview in your browser. Edit your HTML and see changes instantly — no build step, no compilation.

3

[Navigate to header](https://hyperframes.heygen.com/introduction#)

Render to MP4

Run `npx hyperframes render --output output.mp4` to produce a final video. The engine seeks each frame in headless Chrome, captures it with `beginFrame`, and pipes the result through FFmpeg. Run locally or in Docker for fully reproducible output.

## [​](https://hyperframes.heygen.com/introduction\#packages)  Packages

[**@hyperframes/core** \\
\\
Types, HTML parsing, runtime, and composition linter — the foundation everything else builds on.](https://hyperframes.heygen.com/packages/core)

[**@hyperframes/engine** \\
\\
Seekable page-to-video capture engine. Loads HTML in headless Chrome and captures frame-by-frame.](https://hyperframes.heygen.com/packages/engine)

[**@hyperframes/producer** \\
\\
Full rendering pipeline combining capture and FFmpeg encoding into a single API call.](https://hyperframes.heygen.com/packages/producer)

[**@hyperframes/studio** \\
\\
Visual composition editor UI for building and previewing timelines interactively.](https://hyperframes.heygen.com/packages/studio)

[**hyperframes (CLI)** \\
\\
Command-line tool for creating, previewing, and rendering compositions.](https://hyperframes.heygen.com/packages/cli)

## [​](https://hyperframes.heygen.com/introduction\#next-steps)  Next Steps

[**Quickstart** \\
\\
Build and render your first video in 60 seconds](https://hyperframes.heygen.com/quickstart)

[**Compositions** \\
\\
Understand the HTML-based data model behind every video](https://hyperframes.heygen.com/concepts/compositions)

[**GSAP Animation** \\
\\
Add timeline-driven animations with GSAP](https://hyperframes.heygen.com/guides/gsap-animation)

[**Rendering** \\
\\
Render locally, in Docker, or in a CI pipeline](https://hyperframes.heygen.com/guides/rendering)

[QuickstartCreate, preview, and render your first Hyperframes video in under two minutes.\\
\\
Next](https://hyperframes.heygen.com/quickstart)

Ctrl+I

On this page

- [See It in Action](https://hyperframes.heygen.com/introduction#see-it-in-action)
- [Why Hyperframes?](https://hyperframes.heygen.com/introduction#why-hyperframes)
- [How It Works](https://hyperframes.heygen.com/introduction#how-it-works)
- [Packages](https://hyperframes.heygen.com/introduction#packages)
- [Next Steps](https://hyperframes.heygen.com/introduction#next-steps)

Assistant

Responses are generated using AI and may contain mistakes.
