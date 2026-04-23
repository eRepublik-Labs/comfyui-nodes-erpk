[Skip to main content](https://hyperframes.heygen.com/packages/engine#content-area)

[HyperFrames home page![light logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/light.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=8fff06fe865e474513624008576b71bb)![dark logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/dark.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=5c0e7bb1b0c720593e3f904b47b9e1a3)](https://hyperframes.heygen.com/)

Search...

⌘KAsk AI

Search...

Navigation

Packages

@hyperframes/engine

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

The engine package provides the low-level video capture pipeline: it loads an HTML page in headless Chrome, seeks to each frame independently, and captures pixel buffers using Chrome’s `HeadlessExperimental.beginFrame` API. This is the layer that makes Hyperframes rendering deterministic.

```
npm install @hyperframes/engine
```

## [​](https://hyperframes.heygen.com/packages/engine\#when-to-use)  When to Use

**Most users should NOT use the engine directly.** Use the [CLI](https://hyperframes.heygen.com/packages/cli) (`npx hyperframes render`) or the [producer](https://hyperframes.heygen.com/packages/producer) package instead — they handle runtime injection, audio mixing, and encoding for you.

**Use `@hyperframes/engine` when you need to:**

- Build a custom rendering pipeline with full control over frame capture
- Integrate Hyperframes capture into an existing video processing system
- Capture individual frames (e.g., for thumbnails or sprite sheets) without encoding to video
- Implement a custom encoding backend (not FFmpeg)

**Use a different package if you want to:**

- Render an HTML composition to a finished MP4 or WebM — use the [producer](https://hyperframes.heygen.com/packages/producer) or [CLI](https://hyperframes.heygen.com/packages/cli)
- Preview compositions in the browser — use the [CLI](https://hyperframes.heygen.com/packages/cli) or [studio](https://hyperframes.heygen.com/packages/studio)
- Lint or parse composition HTML — use [core](https://hyperframes.heygen.com/packages/core)

## [​](https://hyperframes.heygen.com/packages/engine\#how-it-works)  How It Works

The engine implements a **seek-and-capture** loop that is fundamentally different from screen recording:

1

[Navigate to header](https://hyperframes.heygen.com/packages/engine#)

Launch headless Chrome

The engine starts `chrome-headless-shell`, a minimal headless Chrome binary optimized for programmatic control via the Chrome DevTools Protocol (CDP).

2

[Navigate to header](https://hyperframes.heygen.com/packages/engine#)

Load the composition

Your HTML composition is loaded into a browser page. The Hyperframes runtime is injected to manage timeline seeking.

3

[Navigate to header](https://hyperframes.heygen.com/packages/engine#)

Seek to each frame

For every frame in the video (e.g., 900 frames for a 30-second video at 30fps), the engine calls `renderSeek(time)` to advance the composition to the exact timestamp. No wall clock is involved — each frame is independently positioned.

4

[Navigate to header](https://hyperframes.heygen.com/packages/engine#)

Capture via BeginFrame

Chrome’s `HeadlessExperimental.beginFrame` API captures the compositor output as a pixel buffer. This produces pixel-perfect frames without any screen recording artifacts.

5

[Navigate to header](https://hyperframes.heygen.com/packages/engine#)

Hand off frames

Captured frame buffers are passed to a consumer — typically FFmpeg (via the producer) for encoding into MP4, but you can provide your own consumer.

This approach guarantees [deterministic rendering](https://hyperframes.heygen.com/concepts/determinism): the same HTML always produces the identical video, regardless of system load or timing.

## [​](https://hyperframes.heygen.com/packages/engine\#configuration)  Configuration

```
import { resolveConfig, DEFAULT_CONFIG } from '@hyperframes/engine';
import type { EngineConfig } from '@hyperframes/engine';

// Use defaults
const config = DEFAULT_CONFIG;

// Or resolve with overrides
const config = resolveConfig({
  // ... custom options
});
```

### [​](https://hyperframes.heygen.com/packages/engine\#quality-presets)  Quality Presets

| Preset | Use Case | Speed |
| --- | --- | --- |
| `draft` | Fast iteration during development | Fastest |
| `standard` | Production renders with good quality/speed balance | Moderate |
| `high` | Final delivery, maximum quality | Slowest |

### [​](https://hyperframes.heygen.com/packages/engine\#fps-options)  FPS Options

| FPS | Use Case |
| --- | --- |
| `24` | Cinematic look, smaller file size |
| `30` | Standard web video, good balance |
| `60` | Smooth motion, UI animations, screen recordings |

## [​](https://hyperframes.heygen.com/packages/engine\#programmatic-usage)  Programmatic Usage

The engine uses a session-based API for frame capture:

```
import {
  createCaptureSession,
  initializeSession,
  captureFrame,
  captureFrameToBuffer,
  getCompositionDuration,
  closeCaptureSession,
} from '@hyperframes/engine';

// 1. Create a capture session
const session = await createCaptureSession({ fps: 30, width: 1920, height: 1080 });

// 2. Initialize with a composition
await initializeSession(session, './my-video/index.html');

// 3. Get the total duration
const duration = getCompositionDuration(session);

// 4. Capture frames
const totalFrames = Math.ceil(duration * 30);
for (let i = 0; i < totalFrames; i++) {
  // Capture to disk
  const result = await captureFrame(session, i);
  // result.path, result.captureTimeMs

  // Or capture to buffer (in-memory)
  const bufResult = await captureFrameToBuffer(session, i);
  // bufResult.buffer, bufResult.captureTimeMs
}

// 5. Clean up
await closeCaptureSession(session);
```

### [​](https://hyperframes.heygen.com/packages/engine\#browser-management)  Browser Management

```
import {
  acquireBrowser,
  releaseBrowser,
  resolveHeadlessShellPath,
  buildChromeArgs,
} from '@hyperframes/engine';

// Acquire a browser instance (creates or reuses from pool)
const browser = await acquireBrowser();

// Get the Chrome binary path
const chromePath = await resolveHeadlessShellPath();

// Release when done
await releaseBrowser(browser);
```

### [​](https://hyperframes.heygen.com/packages/engine\#encoding)  Encoding

The engine includes FFmpeg encoding utilities with support for MP4 (h264) and WebM (VP9 with alpha):

```
import {
  encodeFramesFromDir,
  muxVideoWithAudio,
  applyFaststart,
  detectGpuEncoder,
  getEncoderPreset,
  ENCODER_PRESETS,
} from '@hyperframes/engine';

// Get format-aware encoder settings
const mp4Preset = getEncoderPreset('standard', 'mp4');
// { codec: "h264", pixelFormat: "yuv420p", preset: "medium", quality: 23 }

const webmPreset = getEncoderPreset('standard', 'webm');
// { codec: "vp9", pixelFormat: "yuva420p", preset: "good", quality: 23 }

// Encode captured frames to video
await encodeFramesFromDir(framesDir, 'frame_%06d.png', outputPath, {
  fps: 30,
  ...webmPreset,
});

// Mix video with audio (uses Opus for WebM, AAC for MP4)
await muxVideoWithAudio(videoPath, audioPath, outputPath);

// Apply MP4 faststart for streaming (no-op for WebM)
await applyFaststart(inputPath, outputPath);

// Detect GPU encoding support
const gpu = await detectGpuEncoder();
// gpu: "nvenc" | "videotoolbox" | "vaapi" | null
```

#### [​](https://hyperframes.heygen.com/packages/engine\#webm-with-vp9-alpha)  WebM with VP9 Alpha

When encoding for transparency, use `format: "webm"` with `getEncoderPreset()`. This configures:

- **VP9 codec** (`libvpx-vp9`) with alpha-capable `yuva420p` pixel format
- **`-auto-alt-ref 0`** and **`alpha_mode=1`** metadata for proper alpha encoding
- **`-row-mt 1`** for multi-threaded VP9 encoding
- **Opus audio** in the mux step (instead of AAC for MP4)

### [​](https://hyperframes.heygen.com/packages/engine\#streaming-encoder)  Streaming Encoder

For memory-efficient encoding without writing frames to disk:

```
import { spawnStreamingEncoder } from '@hyperframes/engine';

const encoder = await spawnStreamingEncoder({
  outputPath: './output.mp4',
  fps: 30,
  width: 1920,
  height: 1080,
});

// Feed frames directly to encoder
encoder.writeFrame(frameBuffer);
// ...
const result = await encoder.finalize();
```

### [​](https://hyperframes.heygen.com/packages/engine\#video-frame-extraction)  Video Frame Extraction

Extract frames from source video files for injection into the browser:

```
import {
  parseVideoElements,
  extractAllVideoFrames,
  getFrameAtTime,
  createFrameLookupTable,
  FrameLookupTable,
} from '@hyperframes/engine';

// Parse video elements from HTML
const videos = parseVideoElements(html);

// Extract all frames from a video
const frames = await extractAllVideoFrames(videoPath, { fps: 30 });

// Create a lookup table for fast frame access
const lookup = createFrameLookupTable(frames);
const frame = lookup.getFrameAtTime(5.0);
```

### [​](https://hyperframes.heygen.com/packages/engine\#audio-processing)  Audio Processing

```
import { parseAudioElements, processCompositionAudio } from '@hyperframes/engine';

// Parse audio elements from HTML
const audioElements = parseAudioElements(html);

// Process and mix all audio tracks
const mixResult = await processCompositionAudio({ audioElements, duration, fps });
```

### [​](https://hyperframes.heygen.com/packages/engine\#parallel-rendering)  Parallel Rendering

```
import {
  calculateOptimalWorkers,
  distributeFrames,
  executeParallelCapture,
  getSystemResources,
} from '@hyperframes/engine';

// Check system resources
const resources = getSystemResources();

// Calculate optimal worker count
const workers = calculateOptimalWorkers(totalFrames);

// Distribute frames across workers
const tasks = distributeFrames(totalFrames, workers);

// Execute parallel capture
const results = await executeParallelCapture(tasks);
```

### [​](https://hyperframes.heygen.com/packages/engine\#file-server)  File Server

Serve composition files over HTTP for the browser to load:

```
import { createFileServer } from '@hyperframes/engine';

const server = await createFileServer({ root: './my-video', port: 0 });
// server.url, server.port
// ... use server.url as the composition URL
await server.close();
```

## [​](https://hyperframes.heygen.com/packages/engine\#hdr-apis)  HDR APIs

The engine exports two layers of HDR support: **color-space utilities** that classify sources and configure the FFmpeg encoder, and a **WebGPU readback runtime** for capturing CSS-animated DOM directly into HDR.For end-to-end HDR rendering (HDR video and image sources composited into an HDR10 MP4) use the [producer](https://hyperframes.heygen.com/packages/producer) or the CLI’s `--hdr` flag — see [HDR Rendering](https://hyperframes.heygen.com/guides/hdr). The APIs below are for custom integrations.

### [​](https://hyperframes.heygen.com/packages/engine\#color-space-utilities)  Color space utilities

```
import {
  isHdrColorSpace,
  detectTransfer,
  analyzeCompositionHdr,
  getHdrEncoderColorParams,
  DEFAULT_HDR10_MASTERING,
} from '@hyperframes/engine';
import type { HdrTransfer, HdrEncoderColorParams, HdrMasteringMetadata } from '@hyperframes/engine';

// Classify a single source from its ffprobe color space
isHdrColorSpace(colorSpace);          // boolean — true for BT.2020 / PQ / HLG
detectTransfer(colorSpace);           // 'pq' | 'hlg' (gate on isHdrColorSpace first)

// Pick the dominant transfer across many sources
analyzeCompositionHdr([cs1, cs2]);    // { hasHdr, dominantTransfer: 'pq' | 'hlg' | null }

// Build the FFmpeg color params + HDR10 static metadata for x265
const params = getHdrEncoderColorParams('pq');
// {
//   colorPrimaries: 'bt2020',
//   colorTrc: 'smpte2084',
//   colorspace: 'bt2020nc',
//   pixelFormat: 'yuv420p10le',
//   x265ColorParams: 'colorprim=bt2020:transfer=smpte2084:colormatrix=bt2020nc:master-display=...:max-cll=1000,400',
//   mastering: { masterDisplay: '...', maxCll: '1000,400' },
// }
```

`getHdrEncoderColorParams` always includes both color tagging _and_ the HDR10 static metadata (mastering display + content light level). Without that metadata, downstream players treat the file as SDR BT.2020 and tone-map incorrectly. Pass a custom `HdrMasteringMetadata` if you have measured per-content values; otherwise the conservative `DEFAULT_HDR10_MASTERING` defaults match how most HDR10 grading suites tag content.

### [​](https://hyperframes.heygen.com/packages/engine\#webgpu-hdr-dom-capture)  WebGPU HDR DOM capture

For capturing CSS-animated DOM directly into HDR (no FFmpeg source involved), the engine exposes a separate WebGPU pipeline:

```
import {
  launchHdrBrowser,
  buildHdrChromeArgs,
  initHdrReadback,
  uploadAndReadbackHdrFrame,
  float16ToPqRgb,
} from '@hyperframes/engine';

// Launch headed Chrome with WebGPU enabled
const { browser, page } = await launchHdrBrowser({ width: 1920, height: 1080 });

// Inject the WebGPU readback runtime
const ok = await initHdrReadback(page, 1920, 1080);

// For each frame: upload float16 pixels, read back float16 RGBA
const { rgba16, bytesPerRow } = await uploadAndReadbackHdrFrame(page, float16Base64);

// Convert linear float16 → PQ-encoded 16-bit RGB suitable for piping into ffmpeg/x265
const pqRgb = float16ToPqRgb(rgba16, width, height, bytesPerRow);
```

This path requires **headed Chrome with `--enable-unsafe-webgpu`** — WebGPU is unavailable in `chrome-headless-shell`. It is _not_ used by the default `--hdr` render pipeline (which extracts HDR pixels from sources via FFmpeg and composites in Node). Use it only for advanced custom pipelines that need CSS animations driving HDR pixel output.

## [​](https://hyperframes.heygen.com/packages/engine\#the-window-__hf-protocol)  The `window.__hf` Protocol

The engine communicates with the browser page via the `window.__hf` protocol. Any page that implements this protocol can be captured by the engine — you are not limited to Hyperframes compositions.

```
// The page must expose this on window.__hf
interface HfProtocol {
  duration: number;                  // Total duration in seconds
  seek(time: number): void;         // Seek to a specific time
  media?: HfMediaElement[];         // Optional media element declarations
}

interface HfMediaElement {
  elementId: string;                 // DOM element ID
  src: string;                       // Media source URL
  startTime: number;                 // Start time on timeline
  endTime: number;                   // End time on timeline
  mediaOffset?: number;              // Playback offset in source
  volume?: number;                   // Volume (0-1)
  hasAudio?: boolean;                // Whether element has audio
}
```

## [​](https://hyperframes.heygen.com/packages/engine\#key-concepts)  Key Concepts

### [​](https://hyperframes.heygen.com/packages/engine\#beginframe-rendering)  BeginFrame Rendering

Traditional screen capture records at wall-clock speed — if your system is under load, frames get dropped. The engine uses Chrome’s `HeadlessExperimental.beginFrame` to explicitly advance the compositor, producing each frame on demand. This means:

- **No dropped frames** — every frame is captured
- **No timing dependency** — a 60-second video does not take 60 seconds to capture
- **Pixel-perfect output** — the compositor produces the exact pixels it would display

For more on how this enables deterministic output, see [Deterministic Rendering](https://hyperframes.heygen.com/concepts/determinism).

### [​](https://hyperframes.heygen.com/packages/engine\#seek-contract)  Seek Contract

The engine relies on the Hyperframes runtime’s `renderSeek(time)` function. When called, `renderSeek`:

1. Pauses all GSAP timelines
2. Seeks every timeline to the exact timestamp
3. Updates all media elements (video, audio) to match
4. Mounts/unmounts clips based on their `data-start` and `data-duration`

This contract is what makes frame-by-frame capture possible — each frame is a complete, independent snapshot of the composition at that point in time.

### [​](https://hyperframes.heygen.com/packages/engine\#chrome-requirements)  Chrome Requirements

The engine requires `chrome-headless-shell`, which is included when you install the package. It uses a pinned Chrome version to ensure consistent rendering across environments. For fully deterministic output (including fonts), use Docker mode via the [producer](https://hyperframes.heygen.com/packages/producer).

## [​](https://hyperframes.heygen.com/packages/engine\#related-packages)  Related Packages

## Producer

Wraps the engine with runtime injection, FFmpeg encoding, and audio mixing for complete MP4 output.

## Core

Provides the types, runtime, and linter that the engine depends on.

## CLI

The easiest way to render — calls the producer (and engine) under the hood.

## Studio

Visual editor for building compositions before rendering them with the engine.

[Previous](https://hyperframes.heygen.com/packages/core) [@hyperframes/playerEmbeddable web component for playing HyperFrames compositions in any web page.\\
\\
Next](https://hyperframes.heygen.com/packages/player)

⌘I

On this page

- [When to Use](https://hyperframes.heygen.com/packages/engine#when-to-use)
- [How It Works](https://hyperframes.heygen.com/packages/engine#how-it-works)
- [Configuration](https://hyperframes.heygen.com/packages/engine#configuration)
- [Quality Presets](https://hyperframes.heygen.com/packages/engine#quality-presets)
- [FPS Options](https://hyperframes.heygen.com/packages/engine#fps-options)
- [Programmatic Usage](https://hyperframes.heygen.com/packages/engine#programmatic-usage)
- [Browser Management](https://hyperframes.heygen.com/packages/engine#browser-management)
- [Encoding](https://hyperframes.heygen.com/packages/engine#encoding)
- [WebM with VP9 Alpha](https://hyperframes.heygen.com/packages/engine#webm-with-vp9-alpha)
- [Streaming Encoder](https://hyperframes.heygen.com/packages/engine#streaming-encoder)
- [Video Frame Extraction](https://hyperframes.heygen.com/packages/engine#video-frame-extraction)
- [Audio Processing](https://hyperframes.heygen.com/packages/engine#audio-processing)
- [Parallel Rendering](https://hyperframes.heygen.com/packages/engine#parallel-rendering)
- [File Server](https://hyperframes.heygen.com/packages/engine#file-server)
- [HDR APIs](https://hyperframes.heygen.com/packages/engine#hdr-apis)
- [Color space utilities](https://hyperframes.heygen.com/packages/engine#color-space-utilities)
- [WebGPU HDR DOM capture](https://hyperframes.heygen.com/packages/engine#webgpu-hdr-dom-capture)
- [The window.\_\_hf Protocol](https://hyperframes.heygen.com/packages/engine#the-window-__hf-protocol)
- [Key Concepts](https://hyperframes.heygen.com/packages/engine#key-concepts)
- [BeginFrame Rendering](https://hyperframes.heygen.com/packages/engine#beginframe-rendering)
- [Seek Contract](https://hyperframes.heygen.com/packages/engine#seek-contract)
- [Chrome Requirements](https://hyperframes.heygen.com/packages/engine#chrome-requirements)
- [Related Packages](https://hyperframes.heygen.com/packages/engine#related-packages)

Assistant

Responses are generated using AI and may contain mistakes.
