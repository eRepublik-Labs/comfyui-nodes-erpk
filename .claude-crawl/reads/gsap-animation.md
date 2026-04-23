[Skip to main content](https://hyperframes.heygen.com/guides/gsap-animation#content-area)

[HyperFrames home page![light logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/light.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=8fff06fe865e474513624008576b71bb)![dark logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/dark.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=5c0e7bb1b0c720593e3f904b47b9e1a3)](https://hyperframes.heygen.com/)

Search...

⌘KAsk AI

Search...

Navigation

Guides

GSAP Animation

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

Hyperframes uses [GSAP](https://gsap.com/) for animation. Timelines are paused and controlled by the runtime — you define the animations, the framework handles playback. For background on how animation runtimes plug into Hyperframes, see [Frame Adapters](https://hyperframes.heygen.com/concepts/frame-adapters).

## [​](https://hyperframes.heygen.com/guides/gsap-animation\#setup)  Setup

Include GSAP and create a paused timeline:

index.html

```
<script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>
<script>
  // 1. Create a paused timeline — the framework controls playback
  const tl = gsap.timeline({ paused: true });

  // 2. Add animations using the position parameter (3rd arg) for absolute timing
  tl.to("#title", { opacity: 1, duration: 0.5 }, 0);

  // 3. Initialize the global timelines registry (if not already present)
  window.__timelines = window.__timelines || {};

  // 4. Register the timeline using the data-composition-id as the key
  window.__timelines["root"] = tl;
</script>
```

The key you use in `window.__timelines` must match the `data-composition-id` attribute on your composition’s root element. See [Compositions](https://hyperframes.heygen.com/concepts/compositions) for how the root element is structured.

## [​](https://hyperframes.heygen.com/guides/gsap-animation\#key-rules)  Key Rules

1. **Always create timelines with `{ paused: true }`** — the framework controls playback via [deterministic seeking](https://hyperframes.heygen.com/concepts/determinism)
2. **Register timelines on `window.__timelines`** with the [`data-composition-id`](https://hyperframes.heygen.com/concepts/data-attributes#composition-attributes) as key
3. **Use the position parameter** (3rd argument) for absolute timing: `tl.to(el, vars, 1.5)`
4. **Only animate visual properties** — never control media playback in scripts

## [​](https://hyperframes.heygen.com/guides/gsap-animation\#supported-methods)  Supported Methods

| Method | Description |
| --- | --- |
| `tl.to(target, vars, position)` | Animate to values |
| `tl.from(target, vars, position)` | Animate from values |
| `tl.fromTo(target, fromVars, toVars, position)` | Animate from/to values |
| `tl.set(target, vars, position)` | Set values instantly |

## [​](https://hyperframes.heygen.com/guides/gsap-animation\#supported-properties)  Supported Properties

`opacity`, `x`, `y`, `scale`, `scaleX`, `scaleY`, `rotation`, `width`, `height`, `visibility`, `color`, `backgroundColor`, and any CSS-animatable property.

## [​](https://hyperframes.heygen.com/guides/gsap-animation\#timeline-duration-and-composition-duration)  Timeline Duration and Composition Duration

A composition’s duration equals its GSAP timeline duration. The two are directly linked:

compositions/intro-anim.html

```
// Your last animation ends at 3 seconds...
tl.from("#title", { opacity: 0, y: -50, duration: 1 }, 0);
tl.to("#title", { opacity: 0, duration: 1 }, 2);
// ...so this composition is exactly 3 seconds long.
```

If your composition contains a video clip that is 283 seconds long, but your last GSAP animation ends at 8 seconds, the composition will be only 8 seconds long and the video will be cut short. To extend the timeline to match the video:

index.html

```
// All your visual animations
tl.to("#lower-third", { left: -640, duration: 0.6 }, 7.2);

// Extend the timeline to 283 seconds to match the video length.
// This adds a zero-duration tween at 283s without affecting any elements.
tl.set({}, {}, 283);
```

This is one of the most common mistakes in Hyperframes. If your video cuts off early, the timeline is too short. See [Common Mistakes: Composition Duration Shorter Than Video](https://hyperframes.heygen.com/guides/common-mistakes) for more details.

## [​](https://hyperframes.heygen.com/guides/gsap-animation\#what-not-to-do)  What NOT to Do

These patterns will break your composition or cause sync issues:

index.html

```
// WRONG: Playing media in scripts — the framework owns media playback
document.getElementById("el-video").play();
document.getElementById("el-audio").currentTime = 5;

// WRONG: Creating a non-paused timeline
const tl = gsap.timeline(); // missing { paused: true }!

// WRONG: Animating dimensions directly on a <video> element
tl.to("#el-video", { width: 500, height: 280 }, 5);

// WRONG: Manually nesting sub-timelines
const masterTL = window.__timelines["root"];
masterTL.add(window.__timelines["intro-anim"], 0);
```

The framework automatically manages [media playback](https://hyperframes.heygen.com/reference/html-schema#framework-managed-behavior), [clip lifecycle](https://hyperframes.heygen.com/concepts/compositions#two-layers-primitives-and-scripts), and [sub-composition nesting](https://hyperframes.heygen.com/guides/gsap-animation#sub-composition-timelines). Scripts that duplicate this behavior will conflict.

## [​](https://hyperframes.heygen.com/guides/gsap-animation\#sub-composition-timelines)  Sub-Composition Timelines

Each [nested composition](https://hyperframes.heygen.com/concepts/compositions#nested-compositions) registers its own timeline. The framework automatically nests sub-composition timelines into the parent based on [`data-start`](https://hyperframes.heygen.com/concepts/data-attributes#timing-attributes):

compositions/intro-anim.html

```
// In compositions/intro-anim.html
const tl = gsap.timeline({ paused: true });
tl.from(".title", { opacity: 0, y: -50, duration: 1 });
window.__timelines["intro-anim"] = tl;

// DO NOT manually add sub-timelines to the master:
// masterTL.add(window.__timelines["intro-anim"], 0); // UNNECESSARY
```

Don’t animate `width`, `height`, `top`, or `left` directly on `<video>` elements — this can cause the browser to stop rendering frames. Wrap the video in a `<div>` and animate the wrapper instead. See [Common Mistakes](https://hyperframes.heygen.com/guides/common-mistakes) for a detailed explanation.

## [​](https://hyperframes.heygen.com/guides/gsap-animation\#next-steps)  Next Steps

## Compositions

Understand the building blocks that timelines animate

## Frame Adapters

Learn how GSAP plugs into the render pipeline

## Common Mistakes

Avoid pitfalls that break animations

## HTML Schema Reference

Full reference for composition attributes

[Previous](https://hyperframes.heygen.com/guides/hyperframes-vs-remotion) [RenderingRender compositions to MP4, MOV, or WebM locally or in Docker.\\
\\
Next](https://hyperframes.heygen.com/guides/rendering)

⌘I

On this page

- [Setup](https://hyperframes.heygen.com/guides/gsap-animation#setup)
- [Key Rules](https://hyperframes.heygen.com/guides/gsap-animation#key-rules)
- [Supported Methods](https://hyperframes.heygen.com/guides/gsap-animation#supported-methods)
- [Supported Properties](https://hyperframes.heygen.com/guides/gsap-animation#supported-properties)
- [Timeline Duration and Composition Duration](https://hyperframes.heygen.com/guides/gsap-animation#timeline-duration-and-composition-duration)
- [What NOT to Do](https://hyperframes.heygen.com/guides/gsap-animation#what-not-to-do)
- [Sub-Composition Timelines](https://hyperframes.heygen.com/guides/gsap-animation#sub-composition-timelines)
- [Next Steps](https://hyperframes.heygen.com/guides/gsap-animation#next-steps)

Assistant

Responses are generated using AI and may contain mistakes.
