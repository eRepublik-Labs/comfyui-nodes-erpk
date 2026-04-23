[Skip to main content](https://hyperframes.heygen.com/guides/prompting#content-area)

[HyperFrames home page![light logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/light.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=8fff06fe865e474513624008576b71bb)![dark logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/dark.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=5c0e7bb1b0c720593e3f904b47b9e1a3)](https://hyperframes.heygen.com/)

Search...

Ctrl KAsk AI

Search...

Navigation

Guides

Prompt Guide

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

Hyperframes is built for AI agents — compositions are plain HTML, the CLI is non-interactive, and the framework ships [skills](https://github.com/vercel-labs/skills) that teach agents the patterns docs alone don’t cover. This guide shows how to prompt agents effectively once skills are installed — the vocabulary that changes output, the iteration patterns that save time, and the rules that prevent breakage.

## [​](https://hyperframes.heygen.com/guides/prompting\#one-time-setup)  One-time setup

Install the skills in your project (or globally for your agent):

```
npx skills add heygen-com/hyperframes
```

In Claude Code, restart the session after installing. Skills register as **slash commands**:

| Slash command | What it loads |
| --- | --- |
| `/hyperframes` | Composition authoring — HTML structure, timing, captions, TTS, transitions |
| `/hyperframes-cli` | CLI commands — `init`, `lint`, `preview`, `render`, `transcribe`, `tts` |
| `/hyperframes-registry` | Block and component installation via `hyperframes add` |
| `/website-to-hyperframes` | Capture a URL and turn it into a video — full website-to-video pipeline |
| `/gsap` | GSAP animation API — timelines, easing, ScrollTrigger, plugins |

Always prefix Hyperframes prompts with `/hyperframes` (or invoke the skill another way for non-Claude agents). This loads the skill context explicitly so the agent gets composition rules right the first time, instead of relying on whatever it remembers about web video.

## [​](https://hyperframes.heygen.com/guides/prompting\#the-two-prompt-shapes)  The two prompt shapes

Most successful Hyperframes prompts fall into one of two shapes.

### [​](https://hyperframes.heygen.com/guides/prompting\#cold-start-%E2%80%94-describe-the-video)  Cold start — describe the video

You tell the agent what you want from scratch. Best for greenfield work where you have the creative direction in your head.

> Using `/hyperframes`, create a 10-second product intro with a fade-in title over a dark background and subtle background music.

> Make a 9:16 TikTok-style hook video about \[topic\] using `/hyperframes`, with bouncy captions synced to a TTS narration.

Cold-start prompts work best when you specify:

- **Duration** (e.g. “10 seconds”, ”30s”, “5 scenes of 3s each”)
- **Aspect ratio** (“16:9”, “9:16 vertical”, “1:1 square”) — defaults to 1920x1080 otherwise
- **Mood / style** (“minimal Swiss grid”, “warm grain analog”, “high-energy social”)
- **Key elements** (title, lower third, captions, background video, music)

### [​](https://hyperframes.heygen.com/guides/prompting\#warm-start-%E2%80%94-turn-context-into-a-video)  Warm start — turn context into a video

You give the agent something to work with — a URL, a doc, a CSV, a transcript — and ask it to synthesize that into a video. This is where Hyperframes shines because the agent does the research/summarization step _and_ the production step in one flow.

> Take a look at this GitHub repo [https://github.com/heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) and explain its uses and architecture to me using `/hyperframes`.

> Summarize the attached PDF into a 45-second pitch video using `/hyperframes`.

> Read this changelog and turn the top three changes into a 30-second release announcement video using `/hyperframes`.

> Turn this CSV into an animated bar chart race using `/hyperframes`.

Warm-start prompts produce richer, more grounded videos because the agent is writing about _something specific_ instead of inventing copy.

## [​](https://hyperframes.heygen.com/guides/prompting\#iterating)  Iterating

Hyperframes is a conversation. After the first render, talk to the agent the way you’d talk to a video editor — don’t re-prompt from scratch:

> Make the title 2x bigger.

> Swap to dark mode.

> Add a fade-out at the end and a lower third at 0:03 with my name and title.

> The captions are too small and they overlap the lower third. Move them up and shrink them.

> Replace the background music with `assets/track.mp3`.

The agent already has the composition open and the skills loaded — small targeted edits produce better results than long re-specifications.

## [​](https://hyperframes.heygen.com/guides/prompting\#vocabulary-that-changes-output)  Vocabulary that changes output

The skills map natural-language adjectives to specific framework settings. Using the right word gets you the right result without specifying technical details.

### [​](https://hyperframes.heygen.com/guides/prompting\#motion-&-easing)  Motion & easing

Describe how motion should _feel_ and the agent picks the matching GSAP ease:

| Say this | Agent uses | Feels like |
| --- | --- | --- |
| smooth | `power2.out` | Natural deceleration |
| snappy | `power4.out` | Quick and decisive |
| bouncy | `back.out` | Overshoots then settles |
| springy | `elastic.out` | Oscillates into place |
| dramatic | `expo.out` | Fast start, long glide |
| dreamy | `sine.inOut` | Slow, symmetrical |

**Timing shorthand:** fast (0.2s) = energy, medium (0.4s) = professional, slow (0.6s) = luxury, very slow (1–2s) = cinematic.

### [​](https://hyperframes.heygen.com/guides/prompting\#caption-tones)  Caption tones

Describe the _energy_ of your captions and the agent picks matching typography, size, and animation:

| Tone | Typography | Animation | Size range |
| --- | --- | --- | --- |
| Hype | Heavy weight fonts | Scale-pop | 72–96px |
| Corporate | Clean sans-serif | Fade + slide | 56–72px |
| Tutorial | Monospace | Typewriter | 48–64px |
| Storytelling | Serif | Slow fade | 44–56px |
| Social | Rounded, playful | Bounce | 56–80px |

```
"Hype-style captions with scale-pop"
"Calm, elegant subtitles with slow fades"
"Karaoke-style word highlighting"
```

Per-word styling also works:

```
"Make brand names larger with accent color"
"Add bounce to emotional keywords"
"Highlight numbers differently"
```

### [​](https://hyperframes.heygen.com/guides/prompting\#transitions)  Transitions

Every multi-scene composition benefits from transitions. Describe the energy level:

| Energy | CSS option | Shader option |
| --- | --- | --- |
| Calm | Blur crossfade | Cross-warp morph |
| Medium | Push slide | Whip pan |
| High | Zoom through | Glitch, ridged burn |

Or describe by mood:

```
"Warm transitions for this wellness brand"
"Cold, clinical transitions for tech"
"Playful bouncy transitions"
"Dramatic zoom for the reveal"
```

### [​](https://hyperframes.heygen.com/guides/prompting\#audio-reactive-animation)  Audio-reactive animation

Map audio frequency bands to visual properties. The agent uses these defaults:

| Audio band | Maps to | Visual effect |
| --- | --- | --- |
| Bass | `scale` | Pulse on the beat |
| Treble | `glow` | Shimmer intensity |
| Amplitude | `opacity` | Breathing |
| Mids | `shape` | Morphing |

```
"Make the text pulse with the beat"
"Add bass-driven scale to the logo"
"Create glow that responds to treble"
```

Keep audio-reactive effects subtle for text (3–6% intensity). Go bigger for backgrounds (10–30%).

### [​](https://hyperframes.heygen.com/guides/prompting\#marker-highlights)  Marker highlights

Hand-drawn emphasis effects for text:

| Mode | Effect | Best for |
| --- | --- | --- |
| `highlight` | Marker sweep | Key phrases |
| `circle` | Hand-drawn ellipse | Single words |
| `burst` | Radiating lines | Hype moments |
| `scribble` | Chaotic scratch | Crossing out |
| `sketchout` | Rectangle outline | Callouts |

```
"Add a marker highlight sweep on 'revolutionary'"
"Circle this keyword with hand-drawn effect"
"Add burst lines around 'AMAZING'"
```

### [​](https://hyperframes.heygen.com/guides/prompting\#text-to-speech-voices)  Text-to-speech voices

TTS runs locally via Kokoro (no API key needed). Describe the content and the agent picks a voice, or request one directly:

| Content type | Recommended voices |
| --- | --- |
| Product demo | `af_heart`, `af_nova` |
| Tutorial | `am_adam`, `bf_emma` |
| Marketing | `af_sky`, `am_michael` |

```
"Generate narration for this script"
"Create voiceover with a professional female voice"
"Add TTS with British male voice at 1.1x speed"
```

### [​](https://hyperframes.heygen.com/guides/prompting\#rendering-quality)  Rendering quality

| Quality | Use for |
| --- | --- |
| `draft` | Fast iteration |
| `standard` | Review and feedback |
| `high` | Final delivery |

```
"Quick draft render"
"Render at high quality"
"Export as transparent WebM"
```

## [​](https://hyperframes.heygen.com/guides/prompting\#rules-to-know)  Rules to know

The skills enforce these automatically, but if you hand-edit compositions or debug issues, these are the rules that matter:

1. **Register all timelines** on `window.__timelines` — the renderer can’t seek animations it doesn’t know about.
2. **Video elements must be `muted`** — audio goes in separate `<audio>` elements so the renderer can mix it.
3. **No `Math.random()`** — random values produce different frames on each render, breaking determinism. Use a seeded PRNG (e.g. mulberry32) if you need pseudo-random values.
4. **Synchronous timeline construction** — no `async`/`await` or `fetch()` during GSAP timeline setup.
5. **Timed elements need `class="clip"`** — plus `data-start`, `data-duration`, and `data-track-index`.
6. **Add entrance animations to every scene** — elements appearing without animation feel broken on video.
7. **Add transitions between scenes** — jump cuts between scenes are almost always unintentional in composed video.

Rules 1–5 are technical requirements — breaking them produces incorrect renders. Rules 6–7 are best practices that the skills apply by default. You can override them when you have a reason to.

## [​](https://hyperframes.heygen.com/guides/prompting\#anti-patterns)  Anti-patterns

Things that cause friction (or wrong output):

- **Don’t ask for React / Vue components.** Hyperframes compositions are plain HTML with `data-*` attributes and a GSAP timeline. Asking for “a React component for the intro” forces the agent to translate later.
- **Don’t ask for 4K or 60fps unless you need it.** Defaults (1920×1080, 30fps) render fast and look great. Higher specs slow rendering meaningfully.
- **Don’t skip the slash command.** Without `/hyperframes`, the agent may guess at HTML video conventions instead of using the framework’s actual rules (`class="clip"` on timed elements, `window.__timelines` registration, etc.).
- **Don’t paste long error logs into the prompt without context.** Run `npx hyperframes lint` and `npx hyperframes validate` first — lint catches structural issues, validate catches runtime errors (JS exceptions, missing assets, contrast problems).
- **Don’t assume the agent knows your assets.** Mention file paths explicitly (`assets/intro.mp4`, `assets/logo.png`) — the agent will check what’s there but a hint speeds it up.

## [​](https://hyperframes.heygen.com/guides/prompting\#recommended-workflow)  Recommended workflow

1. `npx hyperframes init my-video` — scaffold a project (skills install automatically)
2. Open the project in Claude Code (or Cursor / Codex)
3. Prompt with `/hyperframes` and one of the shapes above
4. `npx hyperframes preview` — watch in the browser as the agent edits
5. Iterate with small targeted prompts
6. `npx hyperframes render --output final.mp4` when you’re happy

## [​](https://hyperframes.heygen.com/guides/prompting\#next-steps)  Next steps

[**Quickstart** \\
\\
Build and render your first video](https://hyperframes.heygen.com/quickstart)

[**Common Mistakes** \\
\\
Pitfalls the linter can’t catch](https://hyperframes.heygen.com/guides/common-mistakes)

[**GSAP Animation** \\
\\
Add fade, slide, scale, and custom animations](https://hyperframes.heygen.com/guides/gsap-animation)

[**Catalog** \\
\\
50+ ready-to-use blocks and components](https://hyperframes.heygen.com/catalog/blocks/data-chart)

[Previous](https://hyperframes.heygen.com/guides/website-to-video) [Hyperframes vs RemotionWhy we built Hyperframes, how it differs from Remotion in practice, and where each tool fits.\\
\\
Next](https://hyperframes.heygen.com/guides/hyperframes-vs-remotion)

Ctrl+I

On this page

- [One-time setup](https://hyperframes.heygen.com/guides/prompting#one-time-setup)
- [The two prompt shapes](https://hyperframes.heygen.com/guides/prompting#the-two-prompt-shapes)
- [Cold start — describe the video](https://hyperframes.heygen.com/guides/prompting#cold-start-%E2%80%94-describe-the-video)
- [Warm start — turn context into a video](https://hyperframes.heygen.com/guides/prompting#warm-start-%E2%80%94-turn-context-into-a-video)
- [Iterating](https://hyperframes.heygen.com/guides/prompting#iterating)
- [Vocabulary that changes output](https://hyperframes.heygen.com/guides/prompting#vocabulary-that-changes-output)
- [Motion & easing](https://hyperframes.heygen.com/guides/prompting#motion-%26-easing)
- [Caption tones](https://hyperframes.heygen.com/guides/prompting#caption-tones)
- [Transitions](https://hyperframes.heygen.com/guides/prompting#transitions)
- [Audio-reactive animation](https://hyperframes.heygen.com/guides/prompting#audio-reactive-animation)
- [Marker highlights](https://hyperframes.heygen.com/guides/prompting#marker-highlights)
- [Text-to-speech voices](https://hyperframes.heygen.com/guides/prompting#text-to-speech-voices)
- [Rendering quality](https://hyperframes.heygen.com/guides/prompting#rendering-quality)
- [Rules to know](https://hyperframes.heygen.com/guides/prompting#rules-to-know)
- [Anti-patterns](https://hyperframes.heygen.com/guides/prompting#anti-patterns)
- [Recommended workflow](https://hyperframes.heygen.com/guides/prompting#recommended-workflow)
- [Next steps](https://hyperframes.heygen.com/guides/prompting#next-steps)

Assistant

Responses are generated using AI and may contain mistakes.
