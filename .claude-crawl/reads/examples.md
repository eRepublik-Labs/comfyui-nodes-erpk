[Skip to main content](https://hyperframes.heygen.com/examples#content-area)

[HyperFrames home page![light logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/light.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=8fff06fe865e474513624008576b71bb)![dark logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/dark.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=5c0e7bb1b0c720593e3f904b47b9e1a3)](https://hyperframes.heygen.com/)

Search...

Ctrl KAsk AI

Search...

Navigation

Getting Started

Examples

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

Hyperframes includes starter examples to help you scaffold compositions quickly. Each example gives you a working project with the correct [composition structure](https://hyperframes.heygen.com/concepts/compositions), [data attributes](https://hyperframes.heygen.com/concepts/data-attributes), and a [GSAP timeline](https://hyperframes.heygen.com/guides/gsap-animation) already wired up.

Terminal

```
npx hyperframes init my-video --example <name>
```

## [​](https://hyperframes.heygen.com/examples\#landscape-templates)  Landscape Templates

**Warm Grain** Branding & lifestyle

**Play Mode** Social media

**Swiss Grid** Corporate & technical

**Kinetic Type** Promos & title cards

**Decision Tree** Explainers & tutorials

**Product Promo** Product showcases

**NYT Graph** Data stories

## [​](https://hyperframes.heygen.com/examples\#portrait-templates)  Portrait Templates

**Vignelli** Headlines & announcements

Looking for a minimal starting point? Use **blank** — it gives you an empty composition with just the scaffolding, no visual design.

Terminal

```
npx hyperframes init my-video --example blank
```

## [​](https://hyperframes.heygen.com/examples\#choosing-an-example)  Choosing an Example

| Example | Style | Format | Best for |
| --- | --- | --- | --- |
| `warm-grain` | Organic, textured | Landscape | Lifestyle, branding, editorial |
| `play-mode` | Energetic, elastic | Landscape | Social media, product launches |
| `swiss-grid` | Clean, structured | Landscape | Corporate, data, technical |
| `kinetic-type` | Dramatic type | Landscape | Promos, intros, title cards |
| `decision-tree` | Diagrammatic | Landscape | Explainers, tutorials |
| `product-promo` | Multi-scene | Landscape | Product showcases, demos |
| `nyt-graph` | Editorial data | Landscape | Data stories, reports |
| `vignelli` | Bold, typographic | Portrait | Headlines, announcements |
| `blank` | Minimal scaffolding | — | Full control, agent-generated |

## [​](https://hyperframes.heygen.com/examples\#example-details)  Example Details

- warm-grain

- play-mode

- swiss-grid

- vignelli

- kinetic-type

- decision-tree

- product-promo

- nyt-graph

- blank


### [​](https://hyperframes.heygen.com/examples\#warm-grain)  warm-grain

Cream-toned aesthetic with grain texture overlay.**What it produces:** A composition with warm color grading, textured grain, and smooth transitions. Includes an intro sub-composition and captions support.

```
my-video/
├── meta.json
├── index.html
├── compositions/
│   ├── intro.html
│   ├── graphics.html
│   └── captions.html
└── assets/
```

### [​](https://hyperframes.heygen.com/examples\#play-mode)  play-mode

Playful elastic animations with bold, energetic motion.

```
my-video/
├── meta.json
├── index.html
├── compositions/
│   ├── intro.html
│   ├── stats.html
│   └── captions.html
└── assets/
```

### [​](https://hyperframes.heygen.com/examples\#swiss-grid)  swiss-grid

Structured grid layout inspired by Swiss/International Typographic Style.

```
my-video/
├── meta.json
├── index.html
├── compositions/
│   ├── intro.html
│   ├── graphics.html
│   └── captions.html
└── assets/
```

### [​](https://hyperframes.heygen.com/examples\#vignelli)  vignelli

Bold typography with red accents (1080×1920 portrait).

```
my-video/
├── meta.json
├── index.html
├── compositions/
│   ├── overlays.html
│   └── captions.html
└── assets/
```

### [​](https://hyperframes.heygen.com/examples\#kinetic-type)  kinetic-type

Bold kinetic typography promo with dramatic text animations.

```
my-video/
├── meta.json
├── index.html
└── compositions/
    └── main-graphics.html
```

### [​](https://hyperframes.heygen.com/examples\#decision-tree)  decision-tree

Animated flowchart with branching paths and progressive reveal.

```
my-video/
├── meta.json
├── index.html
└── compositions/
    └── decision_tree.html
```

### [​](https://hyperframes.heygen.com/examples\#product-promo)  product-promo

Multi-scene product showcase with SVG assets.

```
my-video/
├── meta.json
├── index.html
├── compositions/
│   ├── scene1-logo-intro.html
│   ├── scene2-4-canvas.html
│   └── scene5-logo-outro.html
└── assets/
    ├── figma-cursors.svg
    ├── figma-logo-pieces.svg
    └── figma-logo-pills.svg
```

### [​](https://hyperframes.heygen.com/examples\#nyt-graph)  nyt-graph

Animated data chart in print editorial style.

```
my-video/
├── meta.json
├── index.html
└── compositions/
    └── nyt-chart.html
```

### [​](https://hyperframes.heygen.com/examples\#blank)  blank

Empty composition with just the scaffolding.

```
my-video/
├── meta.json
├── index.html
└── compositions/
    └── captions.html
```

## [​](https://hyperframes.heygen.com/examples\#passing-a-source-video)  Passing a Source Video

Terminal

```
npx hyperframes init my-video --example warm-grain --video ./my-clip.mp4
```

The CLI will probe the video for duration, resolution, and codec. If the video uses an incompatible codec, it will be automatically transcoded to H.264 MP4 if FFmpeg is available.

## [​](https://hyperframes.heygen.com/examples\#custom-examples)  Custom Examples

Any directory with an `index.html` can serve as an example. Your custom example needs:

1. An `index.html` with a [`data-composition-id`](https://hyperframes.heygen.com/concepts/data-attributes#composition-attributes) root element
2. A [GSAP timeline](https://hyperframes.heygen.com/guides/gsap-animation) registered in `window.__timelines`
3. Any assets in the same directory or a subdirectory

index.html

```
<div id="root" data-composition-id="my-example"
     data-start="0" data-width="1920" data-height="1080">

  <!-- Your elements here -->

  <script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>
  <script>
    const tl = gsap.timeline({ paused: true });
    // Add your animations...
    window.__timelines = window.__timelines || {};
    window.__timelines["my-example"] = tl;
  </script>
</div>
```

After creating a custom example, validate it with the [linter](https://hyperframes.heygen.com/packages/cli#lint):

Terminal

```
npx hyperframes lint
```

## [​](https://hyperframes.heygen.com/examples\#next-steps)  Next Steps

[**Quickstart** \\
\\
Create, preview, and render your first video](https://hyperframes.heygen.com/quickstart)

[**GSAP Animation** \\
\\
Add animations to your example](https://hyperframes.heygen.com/guides/gsap-animation)

[**Compositions** \\
\\
Understand the composition data model](https://hyperframes.heygen.com/concepts/compositions)

[**Rendering** \\
\\
Render your composition to MP4](https://hyperframes.heygen.com/guides/rendering)

[Previous](https://hyperframes.heygen.com/quickstart) [CompositionsThe fundamental building block of a Hyperframes video.\\
\\
Next](https://hyperframes.heygen.com/concepts/compositions)

Ctrl+I

On this page

- [Landscape Templates](https://hyperframes.heygen.com/examples#landscape-templates)
- [Portrait Templates](https://hyperframes.heygen.com/examples#portrait-templates)
- [Choosing an Example](https://hyperframes.heygen.com/examples#choosing-an-example)
- [Example Details](https://hyperframes.heygen.com/examples#example-details)
- [warm-grain](https://hyperframes.heygen.com/examples#warm-grain)
- [Passing a Source Video](https://hyperframes.heygen.com/examples#passing-a-source-video)
- [Custom Examples](https://hyperframes.heygen.com/examples#custom-examples)
- [Next Steps](https://hyperframes.heygen.com/examples#next-steps)

Assistant

Responses are generated using AI and may contain mistakes.
