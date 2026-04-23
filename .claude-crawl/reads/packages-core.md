[Skip to main content](https://hyperframes.heygen.com/packages/core#content-area)

[HyperFrames home page![light logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/light.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=8fff06fe865e474513624008576b71bb)![dark logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/dark.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=5c0e7bb1b0c720593e3f904b47b9e1a3)](https://hyperframes.heygen.com/)

Search...

⌘KAsk AI

Search...

Navigation

Packages

@hyperframes/core

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

The core package provides the foundational types, HTML parsing/generation, runtime, and composition linter that all other Hyperframes packages build on. If you are building tooling, writing a custom integration, or extending Hyperframes itself, this is the package you need.

```
npm install @hyperframes/core
```

## [​](https://hyperframes.heygen.com/packages/core\#when-to-use)  When to Use

**Most users do not need to install `@hyperframes/core` directly.** The [CLI](https://hyperframes.heygen.com/packages/cli), [producer](https://hyperframes.heygen.com/packages/producer), and [studio](https://hyperframes.heygen.com/packages/studio) packages all depend on core internally. You only need it if you are doing one of the things listed below.

**Use `@hyperframes/core` when you need to:**

- Lint compositions programmatically (CI pipelines, editor plugins)
- Parse HTML compositions into structured TypeScript objects
- Generate composition HTML from data (e.g., from an API or AI agent)
- Access the Hyperframes type system for your own tooling
- Embed the Hyperframes runtime in a custom player

**Use a different package if you want to:**

- Preview compositions in the browser — use the [CLI](https://hyperframes.heygen.com/packages/cli) (`npx hyperframes preview`) or [studio](https://hyperframes.heygen.com/packages/studio)
- Render compositions to MP4 — use the [CLI](https://hyperframes.heygen.com/packages/cli) (`npx hyperframes render`) or [producer](https://hyperframes.heygen.com/packages/producer)
- Capture frames from a headless browser — use the [engine](https://hyperframes.heygen.com/packages/engine)

## [​](https://hyperframes.heygen.com/packages/core\#package-exports)  Package Exports

The core package has four entry points:

| Import | Description |
| --- | --- |
| `@hyperframes/core` | Types, parsers, generators, adapters, runtime utilities |
| `@hyperframes/core/lint` | Composition linter |
| `@hyperframes/core/compiler` | Timing compiler, HTML compiler, bundler, static guard |
| `@hyperframes/core/runtime` | Pre-built IIFE runtime for browser injection |

## [​](https://hyperframes.heygen.com/packages/core\#types)  Types

The core type system models compositions, timeline elements, and variables:

```
import type {
  TimelineElement,
  TimelineMediaElement,
  TimelineTextElement,
  TimelineCompositionElement,
  TimelineElementType,       // "video" | "image" | "text" | "audio" | "composition"
  CompositionSpec,
  CompositionVariable,
  CanvasResolution,          // "landscape" | "portrait"
  Orientation,               // "16:9" | "9:16"
  FrameAdapter,
  FrameAdapterContext,
} from '@hyperframes/core';

// Type guards
import {
  isTextElement,
  isMediaElement,
  isCompositionElement,
  isStringVariable,
  isNumberVariable,
  isColorVariable,
  isBooleanVariable,
  isEnumVariable,
} from '@hyperframes/core';

// Constants
import {
  CANVAS_DIMENSIONS,        // { landscape: { width, height }, portrait: { width, height } }
  TIMELINE_COLORS,
  DEFAULT_DURATIONS,
} from '@hyperframes/core';
```

### [​](https://hyperframes.heygen.com/packages/core\#variable-types)  Variable Types

Compositions can expose typed variables for dynamic content:

```
import type {
  CompositionVariableType,   // "string" | "number" | "color" | "boolean" | "enum"
  StringVariable,
  NumberVariable,
  ColorVariable,
  BooleanVariable,
  EnumVariable,
} from '@hyperframes/core';
```

### [​](https://hyperframes.heygen.com/packages/core\#keyframe-types)  Keyframe Types

```
import type {
  Keyframe,
  KeyframeProperties,
  ElementKeyframes,
  StageZoom,
  StageZoomKeyframe,
} from '@hyperframes/core';

import { getDefaultStageZoom } from '@hyperframes/core';
```

## [​](https://hyperframes.heygen.com/packages/core\#parsing-and-generating-html)  Parsing and Generating HTML

Round-trip between HTML and structured data:

```
import { parseHtml, generateHyperframesHtml } from '@hyperframes/core';
import type { ParsedHtml, CompositionMetadata } from '@hyperframes/core';

// Parse HTML into structured data
const parsed: ParsedHtml = parseHtml(htmlString);
// parsed.elements, parsed.gsapScript, parsed.styles, parsed.resolution, parsed.keyframes

// Extract composition metadata
import { extractCompositionMetadata } from '@hyperframes/core';
const meta: CompositionMetadata = extractCompositionMetadata(htmlString);
// meta.id, meta.duration, meta.width, meta.height, meta.variables

// Generate HTML from structured data
const html = generateHyperframesHtml(elements, {
  animations,
  styles,
  resolution: 'landscape',
  compositionId: 'my-video',
});
```

### [​](https://hyperframes.heygen.com/packages/core\#modifying-html)  Modifying HTML

```
import {
  updateElementInHtml,
  addElementToHtml,
  removeElementFromHtml,
  validateCompositionHtml,
} from '@hyperframes/core';

// Update an element's properties
const updatedHtml = updateElementInHtml(html, 'el-1', { start: 5 });

// Add a new element
const newHtml = addElementToHtml(html, newElement);

// Remove an element
const cleanHtml = removeElementFromHtml(html, 'el-1');

// Validate HTML structure
const result = validateCompositionHtml(html);
// result.valid, result.errors
```

### [​](https://hyperframes.heygen.com/packages/core\#gsap-script-parsing)  GSAP Script Parsing

```
import {
  parseGsapScript,
  serializeGsapAnimations,
  updateAnimationInScript,
  addAnimationToScript,
  removeAnimationFromScript,
  getAnimationsForElement,
  validateCompositionGsap,
  keyframesToGsapAnimations,
  gsapAnimationsToKeyframes,
  SUPPORTED_PROPS,            // animatable properties
  SUPPORTED_EASES,            // available easing functions
} from '@hyperframes/core';
import type { GsapAnimation, GsapMethod, ParsedGsap } from '@hyperframes/core';

// Parse GSAP script into structured animations
const parsed: ParsedGsap = parseGsapScript(scriptContent);
// parsed.animations, parsed.timelineVar, parsed.preamble, parsed.postamble

// Serialize back to script
const script = serializeGsapAnimations(parsed.animations);
```

### [​](https://hyperframes.heygen.com/packages/core\#html-generation)  HTML Generation

```
import {
  generateHyperframesHtml,
  generateGsapTimelineScript,
  generateHyperframesStyles,
} from '@hyperframes/core';

// Generate a complete HTML composition
const html = generateHyperframesHtml(elements, options);

// Generate just the GSAP script
const script = generateGsapTimelineScript(animations, options);

// Generate CSS styles
const { coreCss, customCss, googleFontsLink } = generateHyperframesStyles(
  elements, 'landscape', customStyles
);
```

### [​](https://hyperframes.heygen.com/packages/core\#template-utilities)  Template Utilities

```
import {
  generateBaseHtml,
  getStageStyles,
  GSAP_CDN,
  BASE_STYLES,
  ELEMENT_BASE_STYLES,
  MEDIA_STYLES,
  TEXT_STYLES,
  ZOOM_CONTAINER_STYLES,
} from '@hyperframes/core';

// Generate base HTML structure for a resolution
const baseHtml = generateBaseHtml('landscape');
const styles = getStageStyles('portrait');
```

## [​](https://hyperframes.heygen.com/packages/core\#linter)  Linter

The composition linter checks for structural issues that would cause rendering failures or unexpected behavior. You can run it from the CLI with `npx hyperframes lint`, or call it programmatically:

```
import { lintHyperframeHtml, lintMediaUrls } from '@hyperframes/core/lint';
import type {
  HyperframeLintResult,
  HyperframeLintFinding,
  HyperframeLintSeverity,     // "error" | "warning"
  HyperframeLinterOptions,
} from '@hyperframes/core/lint';

const result: HyperframeLintResult = lintHyperframeHtml(html, { filePath: 'index.html' });
// result.ok, result.errorCount, result.warningCount, result.findings

for (const finding of result.findings) {
  console.log(finding.severity, finding.code, finding.message);
  // finding.file, finding.selector, finding.elementId, finding.fixHint, finding.snippet
}

// Additional media URL validation
const mediaFindings = lintMediaUrls(result.findings);
```

Detected issues include:

- Missing timeline registration (`window.__timelines`)
- Unmuted video elements (causes autoplay failures)
- Missing `class="clip"` on timed visible elements
- Deprecated attribute names
- Missing composition dimensions (`data-width`, `data-height`)
- Invalid `data-start` references to nonexistent clip IDs

For a full list of what the linter catches and how to fix each issue, see [Common Mistakes](https://hyperframes.heygen.com/guides/common-mistakes) and [Troubleshooting](https://hyperframes.heygen.com/guides/troubleshooting).

## [​](https://hyperframes.heygen.com/packages/core\#compiler)  Compiler

The compiler sub-package handles timing resolution, HTML compilation, and bundling:

```
// Timing compiler (browser-safe — no Node.js dependencies)
import {
  compileTimingAttrs,
  injectDurations,
  extractResolvedMedia,
  clampDurations,
} from '@hyperframes/core/compiler';
import type {
  UnresolvedElement,
  ResolvedDuration,
  ResolvedMediaElement,
  CompilationResult,
} from '@hyperframes/core/compiler';

// Compile timing attributes from HTML
const compiled: CompilationResult = compileTimingAttrs(html);

// Inject resolved durations back into HTML
const updatedHtml = injectDurations(html, compiled.durations);

// Extract resolved media elements
const media: ResolvedMediaElement[] = extractResolvedMedia(html);
```

```
// HTML compiler (Node.js — requires media probing)
import { compileHtml } from '@hyperframes/core/compiler';
import type { MediaDurationProber } from '@hyperframes/core/compiler';

const prober: MediaDurationProber = async (src) => getDuration(src);
const compiledHtml = await compileHtml(html, prober);
```

```
// HTML bundler (Node.js — bundles to single file)
import { bundleToSingleHtml } from '@hyperframes/core/compiler';
import type { BundleOptions } from '@hyperframes/core/compiler';

const bundled = await bundleToSingleHtml({ entryPath: './index.html', inline: true });
```

```
// Static guard — validate HTML contract
import { validateHyperframeHtmlContract } from '@hyperframes/core/compiler';
import type {
  HyperframeStaticGuardResult,
  HyperframeStaticFailureReason,
} from '@hyperframes/core/compiler';

const guard: HyperframeStaticGuardResult = validateHyperframeHtmlContract(html);
// guard.ok, guard.failures[]
// Failure reasons: "missing_composition_id" | "missing_composition_dimensions"
//   | "missing_timeline_registry" | "invalid_script_syntax"
//   | "invalid_static_hyperframe_contract"
```

## [​](https://hyperframes.heygen.com/packages/core\#runtime)  Runtime

The Hyperframes runtime manages playback, seeking, and clip lifecycle in the browser. The core package provides utilities for building and loading the runtime:

```
import {
  loadHyperframeRuntimeSource,
  buildHyperframesRuntimeScript,
  HYPERFRAME_RUNTIME_ARTIFACTS,
  HYPERFRAME_RUNTIME_CONTRACT,
  HYPERFRAME_RUNTIME_GLOBALS,
  HYPERFRAME_BRIDGE_SOURCES,
  HYPERFRAME_CONTROL_ACTIONS,
} from '@hyperframes/core';
import type {
  HyperframeControlAction,
  HyperframesRuntimeBuildOptions,
} from '@hyperframes/core';

// Load the pre-built runtime IIFE
const runtimeSource = loadHyperframeRuntimeSource();

// Build a custom runtime script
const script = buildHyperframesRuntimeScript(options);
```

The pre-built runtime IIFE is available as a direct import:

```
import runtime from '@hyperframes/core/runtime';
```

## [​](https://hyperframes.heygen.com/packages/core\#frame-adapters)  Frame Adapters

The core package defines the [Frame Adapter](https://hyperframes.heygen.com/concepts/frame-adapters) interface and provides the built-in GSAP adapter:

```
import { createGSAPFrameAdapter } from '@hyperframes/core';
import type {
  FrameAdapter,
  FrameAdapterContext,
  GSAPTimelineLike,
  CreateGSAPFrameAdapterOptions,
} from '@hyperframes/core';

// Create a GSAP frame adapter
const adapter: FrameAdapter = createGSAPFrameAdapter({
  id: 'my-composition',
  fps: 30,
  timeline: gsapTimeline,
});

// Adapter lifecycle
await adapter.init?.(context);
const durationFrames = adapter.getDurationFrames();
await adapter.seekFrame(42);
await adapter.destroy?.();
```

## [​](https://hyperframes.heygen.com/packages/core\#media-utilities)  Media Utilities

```
import {
  MEDIA_VISUAL_STYLE_PROPERTIES,
  copyMediaVisualStyles,
  quantizeTimeToFrame,
} from '@hyperframes/core';
import type { MediaVisualStyleProperty } from '@hyperframes/core';

// Quantize a time value to the nearest frame boundary
const frameTime = quantizeTimeToFrame(5.033, 30); // → 5.033... snapped to frame

// Copy visual styles between media elements
copyMediaVisualStyles(fromElement, toElement);
```

## [​](https://hyperframes.heygen.com/packages/core\#picker-api)  Picker API

For element selection in editor UIs:

```
import type {
  HyperframePickerApi,
  HyperframePickerBoundingBox,
  HyperframePickerElementInfo,
} from '@hyperframes/core';
```

## [​](https://hyperframes.heygen.com/packages/core\#related-packages)  Related Packages

## CLI

The easiest way to create, preview, lint, and render compositions.

## Engine

Low-level frame capture pipeline that uses core types and runtime.

## Producer

Full rendering pipeline built on top of core and engine.

## Studio

Visual composition editor that embeds the core runtime for preview.

[@hyperframes/engineSeekable page-to-video capture engine using Chrome's BeginFrame API.\\
\\
Next](https://hyperframes.heygen.com/packages/engine)

⌘I

On this page

- [When to Use](https://hyperframes.heygen.com/packages/core#when-to-use)
- [Package Exports](https://hyperframes.heygen.com/packages/core#package-exports)
- [Types](https://hyperframes.heygen.com/packages/core#types)
- [Variable Types](https://hyperframes.heygen.com/packages/core#variable-types)
- [Keyframe Types](https://hyperframes.heygen.com/packages/core#keyframe-types)
- [Parsing and Generating HTML](https://hyperframes.heygen.com/packages/core#parsing-and-generating-html)
- [Modifying HTML](https://hyperframes.heygen.com/packages/core#modifying-html)
- [GSAP Script Parsing](https://hyperframes.heygen.com/packages/core#gsap-script-parsing)
- [HTML Generation](https://hyperframes.heygen.com/packages/core#html-generation)
- [Template Utilities](https://hyperframes.heygen.com/packages/core#template-utilities)
- [Linter](https://hyperframes.heygen.com/packages/core#linter)
- [Compiler](https://hyperframes.heygen.com/packages/core#compiler)
- [Runtime](https://hyperframes.heygen.com/packages/core#runtime)
- [Frame Adapters](https://hyperframes.heygen.com/packages/core#frame-adapters)
- [Media Utilities](https://hyperframes.heygen.com/packages/core#media-utilities)
- [Picker API](https://hyperframes.heygen.com/packages/core#picker-api)
- [Related Packages](https://hyperframes.heygen.com/packages/core#related-packages)

Assistant

Responses are generated using AI and may contain mistakes.
