[Skip to main content](https://hyperframes.heygen.com/concepts/data-attributes#content-area)

[HyperFrames home page![light logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/light.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=8fff06fe865e474513624008576b71bb)![dark logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/dark.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=5c0e7bb1b0c720593e3f904b47b9e1a3)](https://hyperframes.heygen.com/)

Search...

⌘KAsk AI

Search...

Navigation

Concepts

Data Attributes

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

Hyperframes uses HTML data attributes to control timing, media playback, and [composition](https://hyperframes.heygen.com/concepts/compositions) structure. These are the declarative building blocks of every video.

## [​](https://hyperframes.heygen.com/concepts/data-attributes\#timing-attributes)  Timing Attributes

| Attribute | Example | Description |
| --- | --- | --- |
| `data-start` | `"0"` or `"intro"` | Start time in seconds, or a clip ID reference for [relative timing](https://hyperframes.heygen.com/concepts/data-attributes#relative-timing) |
| `data-duration` | `"5"` | Duration in seconds. Required for images. Optional for video/audio (defaults to source duration). Not used on compositions. |
| `data-track-index` | `"0"` | Timeline track number. Controls z-ordering (higher = in front) and groups clips into rows. Clips on the same track cannot overlap. |

## [​](https://hyperframes.heygen.com/concepts/data-attributes\#media-attributes)  Media Attributes

| Attribute | Example | Description |
| --- | --- | --- |
| `data-media-start` | `"2"` | Media playback offset / trim point in seconds. Default: `0` |
| `data-volume` | `"0.8"` | Audio/video volume, 0 to 1 |
| `data-has-audio` | `"true"` | Indicates video has an audio track |

## [​](https://hyperframes.heygen.com/concepts/data-attributes\#composition-attributes)  Composition Attributes

| Attribute | Example | Description |
| --- | --- | --- |
| `data-composition-id` | `"root"` | Unique ID for [composition](https://hyperframes.heygen.com/concepts/compositions) wrapper (required on every composition) |
| `data-width` | `"1920"` | Composition width in pixels |
| `data-height` | `"1080"` | Composition height in pixels |
| `data-composition-src` | `"./intro.html"` | Path to external [composition](https://hyperframes.heygen.com/concepts/compositions) HTML file |

## [​](https://hyperframes.heygen.com/concepts/data-attributes\#element-visibility)  Element Visibility

Add `class="clip"` to all timed elements so the runtime can manage their visibility lifecycle:

index.html

```
<h1 id="title" class="clip"
    data-start="0" data-duration="5" data-track-index="0">
  Hello World
</h1>
```

## [​](https://hyperframes.heygen.com/concepts/data-attributes\#relative-timing)  Relative Timing

Instead of calculating absolute start times, a clip can reference another clip’s `id` in its `data-start` attribute. This means “start when that clip ends”:

index.html

```
<video id="intro" data-start="0" data-duration="10" data-track-index="0" src="..."></video>
<video id="main" data-start="intro" data-duration="20" data-track-index="0" src="..."></video>
<video id="outro" data-start="main" data-duration="5" data-track-index="0" src="..."></video>
```

`main` resolves to second 10, `outro` resolves to second 30. If `intro`’s duration changes, downstream clips shift automatically.

### [​](https://hyperframes.heygen.com/concepts/data-attributes\#offsets-gaps-and-overlaps)  Offsets (Gaps and Overlaps)

Add `+ N` or `- N` after the ID to offset from the end of the referenced clip:

index.html

```
<!-- 2-second gap after intro -->
<video id="scene-a" data-start="intro + 2" data-duration="20"
       data-track-index="0" src="..."></video>

<!-- 0.5-second overlap with intro (crossfade) -->
<video id="scene-b" data-start="intro - 0.5" data-duration="20"
       data-track-index="1" src="..."></video>
```

Overlapping clips must be on different tracks — clips on the same track cannot overlap in time.

Relative timing rules and constraints

**Same composition only** — references resolve within the clip’s parent [composition](https://hyperframes.heygen.com/concepts/compositions). You cannot reference a clip in a sibling or parent composition.**No circular references** — A cannot start after B if B starts after A. The resolver detects cycles and throws an error.**Referenced clip must have a known duration** — either an explicit `data-duration` or a duration inferred from source media. If the referenced clip has no known duration, the reference cannot resolve.**Parsing rules** — if the value is a valid number, it is treated as absolute seconds. Otherwise it is parsed as one of:

- `<id>` — start when that clip ends
- `<id> + <number>` — start N seconds after that clip ends
- `<id> - <number>` — start N seconds before that clip ends

**Chain length** — references can chain (`A` -\> `B` -\> `C`), but deeply nested chains make the timeline harder to reason about. Keep chains under 3-4 levels for readability.

## [​](https://hyperframes.heygen.com/concepts/data-attributes\#next-steps)  Next Steps

## Compositions

How compositions use data attributes to define video structure

## HTML Schema Reference

Complete attribute reference with per-element details

## GSAP Animation

Animate elements alongside data-attribute-driven timing

## Common Mistakes

Pitfalls to avoid when setting up timing and attributes

[Previous](https://hyperframes.heygen.com/concepts/compositions) [Frame AdaptersBring your own animation runtime to Hyperframes.\\
\\
Next](https://hyperframes.heygen.com/concepts/frame-adapters)

⌘I

On this page

- [Timing Attributes](https://hyperframes.heygen.com/concepts/data-attributes#timing-attributes)
- [Media Attributes](https://hyperframes.heygen.com/concepts/data-attributes#media-attributes)
- [Composition Attributes](https://hyperframes.heygen.com/concepts/data-attributes#composition-attributes)
- [Element Visibility](https://hyperframes.heygen.com/concepts/data-attributes#element-visibility)
- [Relative Timing](https://hyperframes.heygen.com/concepts/data-attributes#relative-timing)
- [Offsets (Gaps and Overlaps)](https://hyperframes.heygen.com/concepts/data-attributes#offsets-gaps-and-overlaps)
- [Next Steps](https://hyperframes.heygen.com/concepts/data-attributes#next-steps)

Assistant

Responses are generated using AI and may contain mistakes.
