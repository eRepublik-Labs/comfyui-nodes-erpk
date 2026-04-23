[Skip to main content](https://hyperframes.heygen.com/concepts/compositions#content-area)

[HyperFrames home page![light logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/light.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=8fff06fe865e474513624008576b71bb)![dark logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/dark.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=5c0e7bb1b0c720593e3f904b47b9e1a3)](https://hyperframes.heygen.com/)

Search...

⌘KAsk AI

Search...

Navigation

Concepts

Compositions

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

A composition is an HTML document that defines a video timeline. Every clip — video, image, audio — lives inside a composition.

## [​](https://hyperframes.heygen.com/concepts/compositions\#structure)  Structure

Every composition needs a root element with `data-composition-id`:

index.html

```
<div id="root" data-composition-id="root"
     data-start="0" data-width="1920" data-height="1080">
  <!-- Elements go here -->
</div>
```

The `index.html` file is the top-level composition. It can contain nested compositions within it. Any composition can be imported into another — there is no special “root” type.

## [​](https://hyperframes.heygen.com/concepts/compositions\#clip-types)  Clip Types

A clip is any discrete block on the timeline, represented as an HTML element with [data attributes](https://hyperframes.heygen.com/concepts/data-attributes):

- `<video>` — Video clips, B-roll, A-roll
- `<img>` — Static images, overlays
- `<audio>` — Music, sound effects
- `<div data-composition-id="...">` — Nested compositions (animations, grouped sequences)

See the [HTML Schema Reference](https://hyperframes.heygen.com/reference/html-schema) for the full list of attributes on each clip type.

## [​](https://hyperframes.heygen.com/concepts/compositions\#nested-compositions)  Nested Compositions

You can embed one composition inside another in two ways: loading from an external file or defining it inline. External files are the recommended approach for reusable compositions.

- External file

- Inline


Reference another HTML file with `data-composition-src`. The framework automatically fetches the file, extracts the `<template>` content, mounts it, executes scripts, and registers the timeline.

index.html

```
<div
  id="el-5"
  data-composition-id="intro-anim"
  data-composition-src="compositions/intro-anim.html"
  data-start="0"
  data-track-index="3"
></div>
```

Each external composition file wraps its content in a `<template>` tag:

compositions/intro-anim.html

```
<template id="intro-anim-template">
  <div data-composition-id="intro-anim" data-width="1920" data-height="1080">
    <div class="title">Welcome!</div>

    <style>
      [data-composition-id="intro-anim"] .title {
        font-size: 72px; color: white; text-align: center;
      }
    </style>

    <script>
      const tl = gsap.timeline({ paused: true });
      tl.from(".title", { opacity: 0, y: -50, duration: 1 });
      window.__timelines["intro-anim"] = tl;
    </script>
  </div>
</template>
```

Define a nested composition directly inside the parent. This is simpler for one-off compositions that do not need to be reused.

index.html

```
<div id="root" data-composition-id="root"
     data-start="0" data-width="1920" data-height="1080">

  <!-- Inline nested composition -->
  <div id="el-5" data-composition-id="intro-anim"
       data-start="0" data-track-index="3"
       data-width="1920" data-height="1080">
    <div class="title">Welcome!</div>
  </div>

  <script>
    // Timeline for the inline composition
    const introTl = gsap.timeline({ paused: true });
    introTl.from(".title", { opacity: 0, y: -50, duration: 1 });
    window.__timelines["intro-anim"] = introTl;
  </script>
</div>
```

Inline compositions do not use `<template>` tags or `data-composition-src`.

### [​](https://hyperframes.heygen.com/concepts/compositions\#project-structure)  Project Structure

project

index.html

compositions

intro-anim.html

caption-overlay.html

outro-title.html

assets

## [​](https://hyperframes.heygen.com/concepts/compositions\#two-layers-primitives-and-scripts)  Two Layers: Primitives and Scripts

Every composition has two layers:

- **HTML** — primitive clips (`video`, `img`, `audio`, nested compositions). The declarative structure: what plays, when, and on which track. Controlled by [data attributes](https://hyperframes.heygen.com/concepts/data-attributes).
- **Script** — effects, transitions, dynamic DOM, canvas, SVG — creative animation via [GSAP](https://hyperframes.heygen.com/guides/gsap-animation). Scripts do **not** control media playback or clip visibility.

Never use scripts to play/pause/seek media elements or to show/hide clips based on timing. The framework handles this automatically from data attributes. Scripts that duplicate this behavior will conflict with the framework. See [Common Mistakes](https://hyperframes.heygen.com/guides/common-mistakes) for examples.

## [​](https://hyperframes.heygen.com/concepts/compositions\#variables)  Variables

Compositions can expose variables for dynamic content:

compositions/card.html

```
<div data-composition-id="card" data-var-title="string" data-var-color="color">
```

Variables make compositions reusable as [examples](https://hyperframes.heygen.com/examples) — the same composition can render different content by injecting variable values at render time.

## [​](https://hyperframes.heygen.com/concepts/compositions\#listing-compositions)  Listing Compositions

Use the [CLI](https://hyperframes.heygen.com/packages/cli) to see all compositions in a project:

```
npx hyperframes compositions
```

## [​](https://hyperframes.heygen.com/concepts/compositions\#next-steps)  Next Steps

## Data Attributes

Full reference for timing, media, and composition attributes

## GSAP Animation

Add animations to your compositions with GSAP timelines

## Examples

Start from built-in examples for common video patterns

## HTML Schema Reference

Complete schema for authoring compositions

[Previous](https://hyperframes.heygen.com/examples) [Data AttributesCore attributes for controlling element timing and behavior.\\
\\
Next](https://hyperframes.heygen.com/concepts/data-attributes)

⌘I

On this page

- [Structure](https://hyperframes.heygen.com/concepts/compositions#structure)
- [Clip Types](https://hyperframes.heygen.com/concepts/compositions#clip-types)
- [Nested Compositions](https://hyperframes.heygen.com/concepts/compositions#nested-compositions)
- [Project Structure](https://hyperframes.heygen.com/concepts/compositions#project-structure)
- [Two Layers: Primitives and Scripts](https://hyperframes.heygen.com/concepts/compositions#two-layers-primitives-and-scripts)
- [Variables](https://hyperframes.heygen.com/concepts/compositions#variables)
- [Listing Compositions](https://hyperframes.heygen.com/concepts/compositions#listing-compositions)
- [Next Steps](https://hyperframes.heygen.com/concepts/compositions#next-steps)

Assistant

Responses are generated using AI and may contain mistakes.
