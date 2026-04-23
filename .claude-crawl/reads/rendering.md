[Skip to main content](https://hyperframes.heygen.com/guides/rendering#content-area)

[HyperFrames home page![light logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/light.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=8fff06fe865e474513624008576b71bb)![dark logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/dark.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=5c0e7bb1b0c720593e3f904b47b9e1a3)](https://hyperframes.heygen.com/)

Search...

Ctrl KAsk AI

Search...

Navigation

Guides

Rendering

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

Render your Hyperframes [compositions](https://hyperframes.heygen.com/concepts/compositions) to MP4, MOV, or WebM with the [CLI](https://hyperframes.heygen.com/packages/cli). The rendering pipeline is frame-by-frame and seek-driven — see [Deterministic Rendering](https://hyperframes.heygen.com/concepts/determinism) for how this works under the hood.

## [​](https://hyperframes.heygen.com/guides/rendering\#getting-started)  Getting Started

1

[Navigate to header](https://hyperframes.heygen.com/guides/rendering#)

Verify your environment

Run the diagnostics command to check for required dependencies:

Terminal

```
npx hyperframes doctor
```

Expected output:

```
✓ Node.js    v22.x
✓ FFmpeg      7.x
✓ FFprobe     7.x
✓ Chrome      (bundled)
✓ Docker      available
```

2

[Navigate to header](https://hyperframes.heygen.com/guides/rendering#)

Preview your composition

Before rendering, preview your composition in the browser to verify it looks correct:

Terminal

```
npx hyperframes preview
```

3

[Navigate to header](https://hyperframes.heygen.com/guides/rendering#)

Render to MP4

Run the render command from your project directory:

Terminal

```
npx hyperframes render --output output.mp4
```

Expected output:

```
⠋ Rendering composition "root" (30fps, standard quality)
✓ Captured 240 frames in 8.2s
✓ Encoded to output.mp4 (8.0s, 1920x1080, 4.2MB)
```

## [​](https://hyperframes.heygen.com/guides/rendering\#rendering-modes)  Rendering Modes

- Local Mode

- Docker Mode


### [​](https://hyperframes.heygen.com/guides/rendering\#local-mode-default)  Local Mode (default)

Uses Puppeteer (bundled Chromium) and your system’s FFmpeg. Fast for iteration during development.**Requires:** FFmpeg installed on your system. See [Troubleshooting](https://hyperframes.heygen.com/guides/troubleshooting) if FFmpeg is not found.

Terminal

```
npx hyperframes render --output output.mp4
```

**Pros:**

- Fast startup, no container overhead
- Uses your system GPU for hardware-accelerated encoding (with `--gpu`)
- Best for iterative development

**Cons:**

- Output may vary across platforms due to font and Chrome version differences
- Not suitable for CI/CD pipelines that require reproducibility

### [​](https://hyperframes.heygen.com/guides/rendering\#docker-mode)  Docker Mode

[Deterministic](https://hyperframes.heygen.com/concepts/determinism) output with an exact Chrome version and font set. Use this for production renders and CI pipelines.**Requires:** Docker installed and running.

Terminal

```
npx hyperframes render --docker --output output.mp4
```

**Pros:**

- Identical output on every platform — same Chrome, same fonts, same FFmpeg
- The same pipeline used in production
- Ideal for CI/CD and automated workflows

**Cons:**

- Slower startup due to container initialization
- No GPU acceleration inside the container

Docker mode uses `chrome-headless-shell` with [BeginFrame](https://hyperframes.heygen.com/concepts/determinism#how-it-works) control for frame-perfect, deterministic capture.

## [​](https://hyperframes.heygen.com/guides/rendering\#when-to-use-each-mode)  When to Use Each Mode

| Scenario | Recommended Mode |
| --- | --- |
| Local development and iteration | Local |
| CI/CD pipeline | Docker |
| Sharing renders with a team | Docker |
| Quick preview export | Local |
| AI agent-driven rendering | Docker |
| Benchmarking performance | Local |

## [​](https://hyperframes.heygen.com/guides/rendering\#options)  Options

| Flag | Values | Default | Description |
| --- | --- | --- | --- |
| `--output` | path | `renders/<name>.mp4` | Output file path |
| `--format` | mp4, mov, webm | mp4 | Output format (see [Transparent Video](https://hyperframes.heygen.com/guides/rendering#transparent-video) below) |
| `--fps` | 24, 30, 60 | 30 | Frames per second |
| `--quality` | draft, standard, high | standard | Encoding quality preset |
| `--crf` | 0–51 | — | Override CRF (lower = higher quality). Cannot combine with `--video-bitrate` |
| `--video-bitrate` | e.g. `10M`, `5000k` | — | Target bitrate encoding. Cannot combine with `--crf` |
| `--workers` | 1-8 or `auto` | auto | Parallel render workers (see [Workers](https://hyperframes.heygen.com/guides/rendering#workers) below) |
| `--max-concurrent-renders` | 1-10 | 2 | Max simultaneous renders via the producer server (see [Concurrent Renders](https://hyperframes.heygen.com/guides/rendering#concurrent-renders) below) |
| `--gpu` | — | off | GPU encoding (NVENC, VideoToolbox, VAAPI) |
| `--hdr` | — | off | Detect HDR sources and output HDR10 (MP4 only). See [HDR Rendering](https://hyperframes.heygen.com/guides/hdr) |
| `--docker` | — | off | Use Docker for [deterministic rendering](https://hyperframes.heygen.com/concepts/determinism) |
| `--quiet` | — | off | Suppress verbose output |

## [​](https://hyperframes.heygen.com/guides/rendering\#quality-and-encoding)  Quality and Encoding

The `--quality` flag selects a preset that controls the H.264 CRF (Constant Rate Factor) and encoder speed:

| Preset | CRF | x264 Preset | Best For |
| --- | --- | --- | --- |
| `draft` | 28 | ultrafast | Quick previews, iteration |
| `standard` | 18 | medium | General use — visually lossless at 1080p |
| `high` | 15 | slow | Final delivery, near-lossless quality |

For finer control, use `--crf` or `--video-bitrate` to override the preset:

```
# Near-lossless quality (CRF 15 = very high quality, large file)
npx hyperframes render --crf 15 --output pristine.mp4

# Target a specific bitrate (useful for size-constrained delivery)
npx hyperframes render --video-bitrate 10M --output controlled.mp4
```

**Tip**: The default `standard` preset (CRF 18) is visually lossless at 1080p — most people cannot distinguish it from the source. Use `--quality draft` for faster iteration, or `--quality high` / `--crf 10` when file size is no concern.

## [​](https://hyperframes.heygen.com/guides/rendering\#workers)  Workers

Each render worker launches a **separate Chrome browser process** to capture frames in parallel. More workers can speed up rendering, but each one consumes ~256 MB of RAM and significant CPU.

### [​](https://hyperframes.heygen.com/guides/rendering\#default-behavior)  Default behavior

By default, Hyperframes uses **half of your CPU cores, capped at 4**:

| Machine | CPU cores | Default workers |
| --- | --- | --- |
| MacBook Air (M1) | 8 | 4 |
| MacBook Pro (M3) | 12 | 4 (capped) |
| 4-core laptop | 4 | 2 |
| 2-core VM | 2 | 1 |

This is intentionally conservative. Each worker spawns its own Chrome process, so the per-worker overhead is significant. Fewer workers avoids resource contention with FFmpeg encoding and your other applications.

### [​](https://hyperframes.heygen.com/guides/rendering\#choosing-a-worker-count)  Choosing a worker count

Terminal

```
# Explicit worker count
npx hyperframes render --workers 1 --output output.mp4

# Let Hyperframes pick based on your CPU
npx hyperframes render --workers auto --output output.mp4

# Maximum parallelism (use with caution on laptops)
npx hyperframes render --workers 8 --output output.mp4
```

Start with the default. If renders feel slow and your system has headroom (check Activity Monitor / `htop`), try increasing `--workers`. If you see high memory pressure or fan noise, reduce it.

### [​](https://hyperframes.heygen.com/guides/rendering\#when-to-use-1-worker)  When to use 1 worker

- Short compositions (under 2 seconds / 60 frames) — parallelism overhead exceeds the benefit
- Low-memory machines (4 GB or less)
- Running renders alongside other heavy processes (video editing, large builds)

### [​](https://hyperframes.heygen.com/guides/rendering\#when-to-increase-workers)  When to increase workers

- Long compositions (30+ seconds) on a machine with 8+ cores and 16+ GB RAM
- Dedicated render machines or CI runners
- Docker mode on a well-provisioned host

## [​](https://hyperframes.heygen.com/guides/rendering\#concurrent-renders)  Concurrent Renders

When multiple render requests hit the producer server simultaneously (common with AI agents), each render spawns its own set of Chrome worker processes. Too many concurrent renders can exhaust CPU and cause failures.The producer server uses a **request-level semaphore** to queue renders. Only `maxConcurrentRenders` renders execute at a time — additional requests wait in a FIFO queue until a slot opens.

### [​](https://hyperframes.heygen.com/guides/rendering\#configuration)  Configuration

Terminal

```
# CLI flag
npx hyperframes render --max-concurrent-renders 2 --output output.mp4

# Environment variable (for the producer server)
PRODUCER_MAX_CONCURRENT_RENDERS=2
```

The default is **2** concurrent renders, which works well on 8-core machines where each render uses 2-3 workers.

### [​](https://hyperframes.heygen.com/guides/rendering\#queue-status)  Queue status

The producer server exposes a `GET /render/queue` endpoint that returns the current state:

```
{
  "maxConcurrentRenders": 2,
  "activeRenders": 1,
  "queuedRenders": 3
}
```

AI agents can poll this endpoint to decide whether to submit a render or wait.

### [​](https://hyperframes.heygen.com/guides/rendering\#sse-queue-events)  SSE queue events

When using the streaming endpoint (`POST /render/stream`), queued requests receive a `queued` event before rendering begins:

```
{"type": "queued", "requestId": "...", "position": 2}
```

This lets agents report “waiting in queue” to users rather than appearing stuck.

### [​](https://hyperframes.heygen.com/guides/rendering\#choosing-a-concurrency-limit)  Choosing a concurrency limit

| Machine | CPU cores | Recommended limit |
| --- | --- | --- |
| 4-core VM | 4 | 1 |
| 8-core workstation | 8 | 2 |
| 16-core server | 16 | 3-4 |
| 32-core render box | 32 | 5-6 |

When in doubt, use 1. Renders will queue up and execute sequentially, but each one gets full CPU and finishes as fast as possible. This is better than 3 renders fighting for CPU and all finishing slowly — or failing.

## [​](https://hyperframes.heygen.com/guides/rendering\#transparent-video)  Transparent Video

Hyperframes supports rendering with a transparent background — useful for overlays, lower thirds, subscribe cards, and any element you want to composite over other footage in a video editor.

### [​](https://hyperframes.heygen.com/guides/rendering\#recommended-format-mov-prores-4444)  Recommended format: MOV (ProRes 4444)

Terminal

```
npx hyperframes render --format mov --output overlay.mov
```

**MOV with ProRes 4444** is the industry standard for transparent video. It works in all major video editors:

- CapCut
- Final Cut Pro
- Adobe Premiere Pro
- DaVinci Resolve
- After Effects

ProRes MOV files are large (typically 5-40 MB for short clips) because ProRes is a high-quality intermediate codec optimized for editing, not delivery. This is expected — the same tradeoff Remotion and professional pipelines make.

### [​](https://hyperframes.heygen.com/guides/rendering\#format-comparison)  Format comparison

| Format | Codec | Transparency | Video editors | Browsers | File size |
| --- | --- | --- | --- | --- | --- |
| **MOV** | ProRes 4444 | Yes | CapCut, Final Cut, Premiere, DaVinci, After Effects | No | Large |
| **WebM** | VP9 | Yes | None (shows black background) | Chrome, Firefox | Small |
| **MP4** | H.264 | No | All | All | Small |

**WebM VP9 alpha** is technically supported but all major video editors ignore the alpha channel and render transparent areas as black. Only Chromium-based browsers (Chrome, Arc, Brave, Edge) decode VP9 alpha correctly. Safari does not support it. Use MOV for editor workflows and WebM only for browser-based playback.

### [​](https://hyperframes.heygen.com/guides/rendering\#how-it-works)  How it works

When you render with `--format mov` or `--format webm`, Hyperframes:

1. Captures each frame as a **PNG with alpha channel** (instead of JPEG for MP4)
2. Sets Chrome’s page background to transparent via `Emulation.setDefaultBackgroundColorOverride`
3. Encodes with an alpha-capable codec (ProRes 4444 for MOV, VP9 for WebM)

Your composition’s HTML should **not** set a `background` on `html` or `body` — leave it unset so the transparent background comes through.

### [​](https://hyperframes.heygen.com/guides/rendering\#authoring-transparent-compositions)  Authoring transparent compositions

```
<style>
  /* Do NOT set background on html/body — leave them transparent */
  * { margin: 0; padding: 0; box-sizing: border-box; }

  [data-composition-id="my-overlay"] {
    position: relative;
    width: 1920px;
    height: 1080px;
    overflow: hidden;
    /* No background here either */
  }
</style>
```

Only the visible elements (cards, text, images) will appear in the final video. Everything else will be transparent.

### [​](https://hyperframes.heygen.com/guides/rendering\#verifying-transparency)  Verifying transparency

- **In a browser:** Open the MOV file — it won’t play (ProRes is not a browser codec). Instead, render a WebM copy and open it in Chrome on a checkerboard background page.
- **In a video editor:** Import the MOV file and place it on a track above other footage. Transparent areas should show the footage below.
- **Online tool:** Use [rotato.app/tools/transparent-video](https://rotato.app/tools/transparent-video) to verify your MOV or WebM has working transparency.

## [​](https://hyperframes.heygen.com/guides/rendering\#tips)  Tips

Use `draft` quality during development for fast previews. Switch to `standard` or `high` for final output.

- Use `npx hyperframes benchmark` to find optimal settings for your system
- Docker mode is slower but guarantees [identical output](https://hyperframes.heygen.com/concepts/determinism) across platforms
- For compositions with many frames, `--gpu` can significantly speed up local encoding

## [​](https://hyperframes.heygen.com/guides/rendering\#next-steps)  Next Steps

[**Deterministic Rendering** \\
\\
Understand the determinism guarantees](https://hyperframes.heygen.com/concepts/determinism)

[**HDR Rendering** \\
\\
Render HDR10 MP4 from HDR video and image sources](https://hyperframes.heygen.com/guides/hdr)

[**CLI Reference** \\
\\
Full list of CLI commands and flags](https://hyperframes.heygen.com/packages/cli)

[**Troubleshooting** \\
\\
Fix common rendering issues](https://hyperframes.heygen.com/guides/troubleshooting)

[Previous](https://hyperframes.heygen.com/guides/gsap-animation) [HDR RenderingRender compositions to HDR10 MP4 (BT.2020 PQ or HLG, 10-bit H.265) when sources contain HDR video or images.\\
\\
Next](https://hyperframes.heygen.com/guides/hdr)

Ctrl+I

On this page

- [Getting Started](https://hyperframes.heygen.com/guides/rendering#getting-started)
- [Rendering Modes](https://hyperframes.heygen.com/guides/rendering#rendering-modes)
- [Local Mode (default)](https://hyperframes.heygen.com/guides/rendering#local-mode-default)
- [When to Use Each Mode](https://hyperframes.heygen.com/guides/rendering#when-to-use-each-mode)
- [Options](https://hyperframes.heygen.com/guides/rendering#options)
- [Quality and Encoding](https://hyperframes.heygen.com/guides/rendering#quality-and-encoding)
- [Workers](https://hyperframes.heygen.com/guides/rendering#workers)
- [Default behavior](https://hyperframes.heygen.com/guides/rendering#default-behavior)
- [Choosing a worker count](https://hyperframes.heygen.com/guides/rendering#choosing-a-worker-count)
- [When to use 1 worker](https://hyperframes.heygen.com/guides/rendering#when-to-use-1-worker)
- [When to increase workers](https://hyperframes.heygen.com/guides/rendering#when-to-increase-workers)
- [Concurrent Renders](https://hyperframes.heygen.com/guides/rendering#concurrent-renders)
- [Configuration](https://hyperframes.heygen.com/guides/rendering#configuration)
- [Queue status](https://hyperframes.heygen.com/guides/rendering#queue-status)
- [SSE queue events](https://hyperframes.heygen.com/guides/rendering#sse-queue-events)
- [Choosing a concurrency limit](https://hyperframes.heygen.com/guides/rendering#choosing-a-concurrency-limit)
- [Transparent Video](https://hyperframes.heygen.com/guides/rendering#transparent-video)
- [Recommended format: MOV (ProRes 4444)](https://hyperframes.heygen.com/guides/rendering#recommended-format-mov-prores-4444)
- [Format comparison](https://hyperframes.heygen.com/guides/rendering#format-comparison)
- [How it works](https://hyperframes.heygen.com/guides/rendering#how-it-works)
- [Authoring transparent compositions](https://hyperframes.heygen.com/guides/rendering#authoring-transparent-compositions)
- [Verifying transparency](https://hyperframes.heygen.com/guides/rendering#verifying-transparency)
- [Tips](https://hyperframes.heygen.com/guides/rendering#tips)
- [Next Steps](https://hyperframes.heygen.com/guides/rendering#next-steps)

Assistant

Responses are generated using AI and may contain mistakes.
