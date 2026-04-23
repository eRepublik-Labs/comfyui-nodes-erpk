\> ## Documentation Index
\> Fetch the complete documentation index at: https://hyperframes.mintlify.app/llms.txt
\> Use this file to discover all available pages before exploring further.

\# @hyperframes/producer

\> Full HTML-to-video rendering pipeline with encoding, audio mixing, and Docker support.

The producer package combines the \[engine's\](/packages/engine) frame capture with FFmpeg encoding to deliver a complete HTML-to-video rendering pipeline. It supports MP4 (h264) and WebM (VP9 with alpha transparency), and handles runtime injection, readiness gates, audio mixing, and optional Docker-based deterministic rendering.

\`\`\`bash theme={null}
npm install @hyperframes/producer
\`\`\`

\## When to Use

\*\*Use \`@hyperframes/producer\` when you need to:\*\*

\\* Render compositions to MP4 or WebM programmatically from Node.js (e.g., in a backend service or CI pipeline)
\\* Build a custom rendering service with fine-grained control over the pipeline
\\* Run visual regression tests against golden baselines
\\* Benchmark render performance across different configurations

\*\*Use a different package if you want to:\*\*

\\* Render from the command line without writing code — use the \[CLI\](/packages/cli) (\`npx hyperframes render\`)
\\* Preview compositions in the browser — use the \[CLI\](/packages/cli) or \[studio\](/packages/studio)
\\* Capture frames without encoding — use the \[engine\](/packages/engine)
\\* Lint or parse composition HTML — use \[core\](/packages/core)

 If you are building a web application or script that just needs to render a video, the \[CLI\](/packages/cli) is the fastest path. The producer package is for when you need programmatic control inside Node.js.

\## What It Does

The producer orchestrates the full render pipeline:

 Reads your \`index.html\` and any referenced sub-compositions.

 Adds the runtime script that manages timeline seeking, clip lifecycle, and media playback.

 Polls for \`window.\_\_playerReady\` and \`window.\_\_renderReady\` to ensure all assets (fonts, images, video) are loaded before capture begins.

 Uses the \[engine's\](/packages/engine) BeginFrame pipeline to capture each frame as a pixel buffer.

 Pipes frame buffers into FFmpeg with the selected quality preset. MP4 uses h264; WebM uses VP9 with alpha transparency support.

 Extracts audio from video clips and audio elements, applies \`data-volume\` and \`data-media-start\` offsets, and mixes them into the final MP4.


\## Programmatic Usage

The producer uses a two-step API: create a render job configuration, then execute it.

\`\`\`typescript theme={null}
import { createRenderJob, executeRenderJob } from '@hyperframes/producer';

const job = createRenderJob({
 input: './my-video/index.html',
 output: './output.mp4',
 fps: 30,
 quality: 'standard',
});

const result = await executeRenderJob(job);
\`\`\`

\### Render Configuration

\`\`\`typescript theme={null}
import type { RenderConfig } from '@hyperframes/producer';

const config: RenderConfig = {
 fps: 30, // 24, 30, or 60
 quality: 'standard', // 'draft', 'standard', or 'high'
 format: 'mp4', // 'mp4' or 'webm' (WebM renders with transparency)
 workers: 4, // Parallel render workers (1-8)
 useGpu: false, // GPU-accelerated encoding
 debug: false, // Debug logging
};
\`\`\`

\#### WebM with Transparency

Set \`format: 'webm'\` to render with a transparent background using VP9 alpha:

\`\`\`typescript theme={null}
const job = createRenderJob({
 fps: 30,
 quality: 'standard',
 format: 'webm',
});

await executeRenderJob(job, './my-overlay', './overlay.webm');
\`\`\`

When \`format: 'webm'\`:

\\* Frames are captured as PNG (preserves alpha channel)
\\* Chrome's page background is set to transparent via CDP
\\* FFmpeg encodes with VP9 + \`yuva420p\` pixel format
\\* Audio is encoded as Opus (instead of AAC for MP4)

\#### HDR Output

Set \`hdr: true\` to enable HDR detection. The producer probes every video and image source for BT.2020 / PQ / HLG color tagging — if any HDR source is found, the output uses H.265 10-bit BT.2020 with HDR10 static metadata. SDR-only compositions are unaffected.

\`\`\`typescript theme={null}
const job = createRenderJob({
 fps: 30,
 quality: 'standard',
 format: 'mp4',
 hdr: true,
});

await executeRenderJob(job, './my-video', './output.mp4');
\`\`\`

When \`hdr: true\`:

\\* Sources are probed via \`ffprobe\`; PQ takes precedence over HLG when both are present
\\* HDR videos and images are extracted as 16-bit linear-light pixels and composited natively
\\* SDR DOM overlays are converted from sRGB → BT.2020 before being layered on top
\\* Output uses \`libx265\` with \`yuv420p10le\` and HDR10 mastering / content-light-level metadata
\\* \`format\` must be \`'mp4'\` — \`'mov'\` and \`'webm'\` fall back to SDR
\\* HDR \`\` support is \*\*still images only\*\*; animated HDR-tagged images use only the first frame

For full details on source requirements, fallback rules, and verification, see \[HDR Rendering\](/guides/hdr).

\### Progress Callbacks

\`\`\`typescript theme={null}
import type { ProgressCallback, RenderStatus } from '@hyperframes/producer';

const onProgress: ProgressCallback = (status: RenderStatus) => {
 console.log(\`Status: ${status}\`);
 // Statuses: "queued" \| "preprocessing" \| "rendering" \| "encoding"
 // \| "assembling" \| "complete" \| "failed" \| "cancelled"
};
\`\`\`

\### Cancellation

\`\`\`typescript theme={null}
import { RenderCancelledError } from '@hyperframes/producer';

try {
 await executeRenderJob(job);
} catch (err) {
 if (err instanceof RenderCancelledError) {
 console.log(\`Cancelled: ${err.reason}\`);
 // reason: "user\_cancelled" \| "timeout" \| "aborted"
 }
}
\`\`\`

\## HTTP Server

The producer includes a built-in HTTP server for running as a rendering service:

\`\`\`typescript theme={null}
import { startServer } from '@hyperframes/producer/server';

await startServer({ port: 8080 });
\`\`\`

\### Server Endpoints

\| Method \| Path \| Description \|
\| \-\-\-\-\-\- \| \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- \| \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- \|
\| \`POST\` \| \`/render\` \| Blocking render — returns JSON result \|
\| \`POST\` \| \`/render/stream\` \| Streaming render with Server-Sent Events \|
\| \`POST\` \| \`/lint\` \| Lint a composition for issues \|
\| \`GET\` \| \`/health\` \| Health check \|
\| \`GET\` \| \`/outputs/:token\` \| Download a rendered MP4 \|

For custom server integration, use the lower-level handlers:

\`\`\`typescript theme={null}
import { createRenderHandlers, createProducerApp } from '@hyperframes/producer/server';

// Get individual request handlers
const handlers = createRenderHandlers(options);

// Or get a full Hono app
const app = createProducerApp(options);
\`\`\`

\## Docker Rendering

For deterministic output, the producer can render inside a Docker container with a pinned Chrome version and font set. This guarantees identical output across machines — critical for CI pipelines and production services.

\`\`\`bash theme={null}
\# Via the CLI (recommended)
npx hyperframes render --docker --output output.mp4
\`\`\`

 Docker mode requires Docker to be installed and running. Run \`npx hyperframes doctor\` to verify your environment. See \[Deterministic Rendering\](/concepts/determinism) for details on what makes Docker mode deterministic.

\## Quality Presets

\| Preset \| Resolution \| Encoding \| Use Case \|
\| \-\-\-\-\-\-\-\-\-\- \| \-\-\-\-\-\-\-\-\-\- \| \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- \| \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- \|
\| \`draft\` \| Original \| Fast CRF \| Quick iteration, previewing edits \|
\| \`standard\` \| Original \| Balanced CRF \| Production renders, sharing \|
\| \`high\` \| Original \| High-quality CRF \| Final delivery, archival \|

\## GPU Encoding

The producer supports hardware-accelerated encoding for faster renders:

\| Platform \| Encoder \| Flag \|
\| \-\-\-\-\-\-\-\- \| \-\-\-\-\-\-\-\-\-\-\-\- \| \-\-\-\-\-\-\-\-\-\-\-\-\- \|
\| NVIDIA \| NVENC \| Auto-detected \|
\| macOS \| VideoToolbox \| Auto-detected \|
\| Linux \| VAAPI \| Auto-detected \|

GPU encoding is automatically used when available. To check your system's capabilities:

\`\`\`bash theme={null}
npx hyperframes doctor
\`\`\`

\## Additional Exports

The producer also re-exports key engine functionality for convenience:

\| Export \| Description \|
\| \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- \| \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- \|
\| \`createCaptureSession()\` \| Create a frame capture session \|
\| \`initializeSession()\` \| Initialize session with a composition \|
\| \`captureFrame()\` / \`captureFrameToBuffer()\` \| Capture individual frames \|
\| \`closeCaptureSession()\` \| Clean up a capture session \|
\| \`getCompositionDuration()\` \| Get total composition duration \|
\| \`getCapturePerfSummary()\` \| Get capture performance metrics \|
\| \`createFileServer()\` \| Create an HTTP file server for serving assets \|
\| \`createVideoFrameInjector()\` \| Create a video frame injector for page \|
\| \`resolveConfig()\` / \`DEFAULT\_CONFIG\` \| Producer configuration \|
\| \`createConsoleLogger()\` / \`defaultLogger\` \| Logging utilities \|
\| \`quantizeTimeToFrame()\` \| Convert time to frame boundary \|
\| \`resolveRenderPaths()\` \| Resolve render directory paths \|
\| \`prepareHyperframeLintBody()\` / \`runHyperframeLint()\` \| Linting utilities \|

\## Regression Testing

The producer includes a regression harness for comparing render output against golden baselines. This is useful for catching visual regressions when changing the runtime, engine, or rendering pipeline.

\`\`\`bash theme={null}
cd packages/producer

\# Build the test Docker image
bun run docker:build:test

\# Run regression tests (compares output against golden baselines)
bun run docker:test

\# Regenerate golden baselines after intentional changes
bun run docker:test:update
\`\`\`

\## Benchmarking

Find optimal render settings for your hardware:

\`\`\`bash theme={null}
\# Via the CLI
npx hyperframes benchmark

\# Directly from the producer package
cd packages/producer
bun run benchmark
\`\`\`

The benchmark runs several compositions with different quality and FPS settings and reports timing for each combination.

\## External assets (files outside \`projectDir\`)

A composition can reference absolute paths to assets outside the project
directory — a local voiceover in \`~/Downloads\`, a shared-drive image, a
generated fixture at an absolute path. The producer handles these by:

1\. \*\*Detection.\*\* During compilation, the HTML compiler walks every
 \`\[src\]\` / \`\[href\]\` and every \`url(...)\` in \`
