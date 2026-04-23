[Skip to main content](https://hyperframes.heygen.com/guides/troubleshooting#content-area)

[HyperFrames home page![light logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/light.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=8fff06fe865e474513624008576b71bb)![dark logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/dark.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=5c0e7bb1b0c720593e3f904b47b9e1a3)](https://hyperframes.heygen.com/)

Search...

⌘KAsk AI

Search...

Navigation

Guides

Troubleshooting

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

If your issue is about a specific coding mistake (animations not working, video cutting off early), see [Common Mistakes](https://hyperframes.heygen.com/guides/common-mistakes) first. This page covers environment, tooling, and rendering issues.

"No composition found"

Your directory needs an `index.html` with a valid [composition](https://hyperframes.heygen.com/concepts/compositions). The root element must have a [`data-composition-id`](https://hyperframes.heygen.com/concepts/data-attributes#composition-attributes) attribute.**Fix:** Run `npx hyperframes init` to create a composition from an [example](https://hyperframes.heygen.com/examples), or verify your `index.html` has the correct structure:

index.html

```
<div id="root" data-composition-id="my-video"
     data-start="0" data-width="1920" data-height="1080">
  <!-- elements here -->
</div>
```

"FFmpeg not found"

Local [rendering](https://hyperframes.heygen.com/guides/rendering) requires FFmpeg installed on your system. Install it for your platform:

macOS

Ubuntu/Debian

Windows

Verify installation

```
brew install ffmpeg
```

After installing, run `npx hyperframes doctor` to verify the CLI can find it.

If you cannot install FFmpeg, use [Docker mode](https://hyperframes.heygen.com/guides/rendering) instead — it bundles FFmpeg inside the container: `npx hyperframes render --docker --output output.mp4`

Lint errors

Run `npx hyperframes lint` to check for common structural issues (see [CLI: lint](https://hyperframes.heygen.com/packages/cli#lint)):

| Error | Meaning |
| --- | --- |
| Missing `data-composition-id` | Root element needs this attribute. See [Compositions](https://hyperframes.heygen.com/concepts/compositions). |
| Missing `class="clip"` | Timed visible elements need this class. See [Data Attributes](https://hyperframes.heygen.com/concepts/data-attributes#element-visibility). |
| Overlapping timelines | Clips on the same [`data-track-index`](https://hyperframes.heygen.com/concepts/data-attributes#timing-attributes) cannot overlap in time. |
| Unmuted video elements | Video elements should be `muted` unless `data-has-audio="true"` is set. |
| Deprecated attribute names | `data-layer` and `data-end` have been replaced. Check the [HTML Schema Reference](https://hyperframes.heygen.com/reference/html-schema). |

Preview not updating

Make sure you are editing the `index.html` in the project directory. The [preview server](https://hyperframes.heygen.com/packages/cli#preview) watches for file changes and auto-reloads.If changes still do not appear:

1. Check the terminal for errors from the preview server
2. Stop and restart `npx hyperframes preview`
3. Hard-refresh the browser: **Ctrl+Shift+R** (Windows/Linux) or **Cmd+Shift+R** (macOS)
4. Clear the browser cache if CSS changes are not reflected

Preview stutters or plays at a low frame rate

**Symptom:** Preview playback is jerky or skips frames, but the rendered mp4 looks fine.**Cause:** Individual frames are taking longer than 16-33ms to paint. Render hides this (it captures frames one at a time), preview does not.**Common culprits, most to least frequent:**

- Stacked `backdrop-filter: blur()` layers, especially at radii above 32px
- Source images at very high resolution (above 4K) displayed in small regions
- `filter: blur()` or `filter: drop-shadow()` on large elements
- Many elements with `box-shadow` or `text-shadow` that also animate

**First thing to check:** does the stutter happen only during specific scenes, or throughout? Scene-specific stutter usually points at an element, often a blur overlay, that becomes visible in that scene.**How to diagnose:** open Chrome DevTools, switch to the Performance tab, record a few seconds of playback, and look for long tasks labeled “Composite Layers” or “Paint”. See [Performance: Measuring a slow composition](https://hyperframes.heygen.com/guides/performance#measuring-a-slow-composition) for the full walkthrough.**Temporary workaround:** render to mp4 and watch the output. Render is accurate regardless of per-frame cost.

Terminal

```
npx hyperframes render --quality draft --output preview.mp4
```

See [Performance](https://hyperframes.heygen.com/guides/performance) for the full guide on expensive CSS patterns and how to fix them.

Render looks different from preview

Use `--docker` mode for [deterministic output](https://hyperframes.heygen.com/concepts/determinism). Local renders may differ due to:

- **Font availability** — different fonts on different platforms cause text reflow
- **Chrome version** — local Chromium vs. Docker’s pinned version can render slightly differently
- **System-specific rendering** — GPU compositing, subpixel antialiasing, etc.

Terminal

```
npx hyperframes render --docker --output output.mp4
```

See [Rendering: When to Use Each Mode](https://hyperframes.heygen.com/guides/rendering#when-to-use-each-mode) for guidance on choosing between local and Docker rendering.

Docker mode fails to start

Verify Docker is installed and the daemon is running:

Terminal

```
docker info
```

Common issues:

- **Docker not running:** Start Docker Desktop or the Docker daemon
- **Permission denied:** Add your user to the `docker` group (`sudo usermod -aG docker $USER`) and restart your shell
- **Image pull fails:** Check your internet connection; the first render downloads the Hyperframes Docker image

Render is slow

Try these optimizations:

1. Use `--quality draft` during development for faster encoding
2. Run `npx hyperframes benchmark` to find the optimal worker count for your system
3. Use `--gpu` for hardware-accelerated encoding (local mode only)
4. Reduce `--fps` to 24 if 30fps is not needed
5. Check that your composition does not have unnecessary elements or overly complex animations

See [Rendering: Options](https://hyperframes.heygen.com/guides/rendering#options) for all available flags.

## [​](https://hyperframes.heygen.com/guides/troubleshooting\#system-diagnostics)  System Diagnostics

Run `npx hyperframes doctor` to check your environment:

Terminal

```
npx hyperframes doctor
```

This checks for Node.js version, FFmpeg availability, Docker status, and other requirements. If `doctor` reports issues, address them before rendering.

## [​](https://hyperframes.heygen.com/guides/troubleshooting\#still-stuck)  Still Stuck?

If none of the above resolves your issue:

1. Run `npx hyperframes info` to gather system and project details
2. Check [GitHub Issues](https://github.com/heygen-com/hyperframes/issues) for similar reports
3. Open a new issue with the output of `npx hyperframes info` and steps to reproduce

## [​](https://hyperframes.heygen.com/guides/troubleshooting\#next-steps)  Next Steps

## Common Mistakes

Coding pitfalls that break compositions

## Rendering

Rendering modes, options, and tips

## CLI Reference

Full list of CLI commands

## Contributing

Report bugs and contribute fixes

[Previous\\
\\
Common MistakesPitfalls that break Hyperframes compositions.](https://hyperframes.heygen.com/guides/common-mistakes)

⌘I

On this page

- [System Diagnostics](https://hyperframes.heygen.com/guides/troubleshooting#system-diagnostics)
- [Still Stuck?](https://hyperframes.heygen.com/guides/troubleshooting#still-stuck)
- [Next Steps](https://hyperframes.heygen.com/guides/troubleshooting#next-steps)

Assistant

Responses are generated using AI and may contain mistakes.
