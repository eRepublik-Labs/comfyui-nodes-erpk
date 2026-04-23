[Skip to main content](https://hyperframes.heygen.com/packages/player#content-area)

[HyperFrames home page![light logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/light.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=8fff06fe865e474513624008576b71bb)![dark logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/dark.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=5c0e7bb1b0c720593e3f904b47b9e1a3)](https://hyperframes.heygen.com/)

Search...

⌘KAsk AI

Search...

Navigation

Packages

@hyperframes/player

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

The player package provides a `<hyperframes-player>` custom element that embeds a HyperFrames composition anywhere — in any framework or plain HTML. Zero dependencies, 3KB gzipped.

```
npm install @hyperframes/player
```

## [​](https://hyperframes.heygen.com/packages/player\#when-to-use)  When to Use

**Use `@hyperframes/player` when you need to:**

- Embed a rendered composition in a website, dashboard, or app
- Add a video-like player to a landing page or product demo
- Show compositions in documentation or blog posts

**Use a different package if you want to:**

- Edit compositions interactively — use the [studio](https://hyperframes.heygen.com/packages/studio)
- Preview during development — use the [CLI](https://hyperframes.heygen.com/packages/cli) (`npx hyperframes preview`)
- Render to MP4 — use the [CLI](https://hyperframes.heygen.com/packages/cli) or [producer](https://hyperframes.heygen.com/packages/producer)

## [​](https://hyperframes.heygen.com/packages/player\#quick-start)  Quick Start

### [​](https://hyperframes.heygen.com/packages/player\#via-cdn)  Via CDN

```
<script src="https://cdn.jsdelivr.net/npm/@hyperframes/player"></script>

<hyperframes-player
  src="./my-composition/index.html"
  controls
  autoplay
  muted
  style="width: 100%; max-width: 800px; aspect-ratio: 16/9"
></hyperframes-player>
```

### [​](https://hyperframes.heygen.com/packages/player\#via-npm)  Via npm

```
import '@hyperframes/player';
```

```
<hyperframes-player src="/compositions/intro.html" controls></hyperframes-player>
```

## [​](https://hyperframes.heygen.com/packages/player\#html-attributes)  HTML Attributes

| Attribute | Type | Default | Description |
| --- | --- | --- | --- |
| `src` | string | required | URL or relative path to composition HTML |
| `width` | number | 1920 | Composition width in pixels |
| `height` | number | 1080 | Composition height in pixels |
| `controls` | boolean | false | Show playback controls overlay |
| `autoplay` | boolean | false | Start playing on load |
| `loop` | boolean | false | Loop playback |
| `muted` | boolean | true | Mute audio (required for autoplay in most browsers) |
| `poster` | string | — | Image URL to show before first play |
| `playback-rate` | number | 1 | Playback speed multiplier |

## [​](https://hyperframes.heygen.com/packages/player\#javascript-api)  JavaScript API

The player mirrors the native `<video>` element API:

```
const player = document.querySelector('hyperframes-player');

// Playback
player.play();
player.pause();
player.seek(2.5); // seek to 2.5 seconds

// Properties
player.currentTime;     // number — current position in seconds
player.currentTime = 5; // seek to 5 seconds
player.duration;        // number — total duration
player.paused;          // boolean
player.ready;           // boolean — true after composition loads
player.playbackRate;    // number — get/set speed
player.muted;           // boolean — get/set mute
player.loop;            // boolean — get/set loop
```

## [​](https://hyperframes.heygen.com/packages/player\#events)  Events

```
const player = document.querySelector('hyperframes-player');

player.addEventListener('ready', (e) => {
  console.log('Duration:', e.detail.duration);
});

player.addEventListener('timeupdate', (e) => {
  console.log('Time:', e.detail.currentTime);
});

player.addEventListener('play', () => console.log('Playing'));
player.addEventListener('pause', () => console.log('Paused'));
player.addEventListener('ended', () => console.log('Ended'));
player.addEventListener('error', (e) => console.error(e.detail.message));
```

| Event | Detail | Description |
| --- | --- | --- |
| `ready` | `{ duration }` | Composition loaded and timeline discovered |
| `timeupdate` | `{ currentTime }` | Fires during playback (~30fps) |
| `play` | — | Playback started |
| `pause` | — | Playback paused |
| `ended` | — | Playback reached end |
| `error` | `{ message }` | Load or runtime error |

## [​](https://hyperframes.heygen.com/packages/player\#framework-examples)  Framework Examples

### [​](https://hyperframes.heygen.com/packages/player\#react)  React

```
import '@hyperframes/player';

function VideoPreview({ src }) {
  return (
    <hyperframes-player
      src={src}
      controls
      style={{ width: '100%', maxWidth: 800 }}
    />
  );
}
```

### [​](https://hyperframes.heygen.com/packages/player\#vue)  Vue

```
<template>
  <hyperframes-player :src="compositionUrl" controls />
</template>

<script setup>
import '@hyperframes/player';
const compositionUrl = './compositions/intro.html';
</script>
```

### [​](https://hyperframes.heygen.com/packages/player\#programmatic)  Programmatic

```
import '@hyperframes/player';

const player = document.createElement('hyperframes-player');
player.src = './my-composition/index.html';
player.controls = true;
player.addEventListener('ready', () => player.play());
document.getElementById('player-container').appendChild(player);
```

## [​](https://hyperframes.heygen.com/packages/player\#advanced-iframe-access)  Advanced: iframe access

The composition runs inside a sandboxed `<iframe>` in the player’s Shadow DOM. For most use cases you don’t need direct access — the JavaScript API and events above are sufficient. But if you’re building an editor, recorder, or custom timeline on top of the player, you’ll need to inspect the composition’s DOM or read its `__player` / `__timelines` runtime objects. The `iframeElement` getter exposes the inner iframe for these consumers:

```
const player = document.querySelector('hyperframes-player');
const iframe = player.iframeElement;

// Reach into the composition's DOM
iframe.contentDocument.querySelectorAll('[data-composition-id]');

// Read the runtime (GSAP timelines, element registry, etc.)
iframe.contentWindow.__timelines;
```

This is the canonical way to bridge the player into editor tools like [`@hyperframes/studio`](https://hyperframes.heygen.com/packages/studio). The studio exports a `resolveIframe` helper that handles both direct iframe refs and web-component refs:

```
import { useTimelinePlayer, resolveIframe } from '@hyperframes/studio';

const { iframeRef } = useTimelinePlayer();
const player = document.createElement('hyperframes-player');
player.setAttribute('src', src);
container.appendChild(player);

// Forward the inner iframe so useTimelinePlayer can drive play/pause/seek.
iframeRef.current = resolveIframe(player);
```

### [​](https://hyperframes.heygen.com/packages/player\#react-declarative-ref-pattern)  React: declarative ref pattern

If you prefer JSX over imperative element creation, attach a ref to the web component and resolve the iframe inside an effect:

```
import '@hyperframes/player';
import type { HyperframesPlayer } from '@hyperframes/player';
import { useTimelinePlayer, resolveIframe } from '@hyperframes/studio';

function StudioPreview({ src }: { src: string }) {
  const { iframeRef, onIframeLoad } = useTimelinePlayer();
  const playerRef = useRef<HyperframesPlayer>(null);

  useEffect(() => {
    iframeRef.current = resolveIframe(playerRef.current);
  });

  return (
    <hyperframes-player
      ref={playerRef}
      src={src}
      onLoad={onIframeLoad}
    />
  );
}
```

**Common gotcha** — if you pass the `<hyperframes-player>` element itself (not `iframeElement`) into a hook or API that expects an `<iframe>`, every `.contentWindow` / `.contentDocument` access returns `null` because the iframe lives inside the player’s Shadow DOM. Timeline seek, play, pause, and DOM inspection all silently no-op. **Always extract `iframeElement` first**, or use `resolveIframe` from `@hyperframes/studio` which handles both iframe and web-component hosts transparently.

## [​](https://hyperframes.heygen.com/packages/player\#architecture)  Architecture

The player uses an iframe inside a Shadow DOM container. This provides:

- **Isolation** — composition CSS/JS can’t leak into or conflict with your page
- **Security** — iframe sandbox restricts composition capabilities
- **Scaling** — auto-scales the composition to fit the player’s container via CSS transforms

The player communicates with the composition via the HyperFrames runtime bridge protocol (`postMessage`). Existing compositions work without modification.

## [​](https://hyperframes.heygen.com/packages/player\#controls)  Controls

When the `controls` attribute is present, a minimal overlay appears at the bottom:

- **Play/Pause** button (left)
- **Scrub bar** with drag support (mouse + touch)
- **Time display** showing current / total duration (right)
- Auto-hides after 3 seconds of inactivity, reappears on hover

[Previous](https://hyperframes.heygen.com/packages/engine) [@hyperframes/producerFull HTML-to-video rendering pipeline with encoding, audio mixing, and Docker support.\\
\\
Next](https://hyperframes.heygen.com/packages/producer)

⌘I

On this page

- [When to Use](https://hyperframes.heygen.com/packages/player#when-to-use)
- [Quick Start](https://hyperframes.heygen.com/packages/player#quick-start)
- [Via CDN](https://hyperframes.heygen.com/packages/player#via-cdn)
- [Via npm](https://hyperframes.heygen.com/packages/player#via-npm)
- [HTML Attributes](https://hyperframes.heygen.com/packages/player#html-attributes)
- [JavaScript API](https://hyperframes.heygen.com/packages/player#javascript-api)
- [Events](https://hyperframes.heygen.com/packages/player#events)
- [Framework Examples](https://hyperframes.heygen.com/packages/player#framework-examples)
- [React](https://hyperframes.heygen.com/packages/player#react)
- [Vue](https://hyperframes.heygen.com/packages/player#vue)
- [Programmatic](https://hyperframes.heygen.com/packages/player#programmatic)
- [Advanced: iframe access](https://hyperframes.heygen.com/packages/player#advanced-iframe-access)
- [React: declarative ref pattern](https://hyperframes.heygen.com/packages/player#react-declarative-ref-pattern)
- [Architecture](https://hyperframes.heygen.com/packages/player#architecture)
- [Controls](https://hyperframes.heygen.com/packages/player#controls)

Assistant

Responses are generated using AI and may contain mistakes.
