\> ## Documentation Index
\> Fetch the complete documentation index at: https://hyperframes.mintlify.app/llms.txt
\> Use this file to discover all available pages before exploring further.

\# HTML Schema Reference

\> Complete reference for authoring Hyperframes HTML compositions.

This is the full schema reference for Hyperframes compositions. For a gentler introduction, see \[Compositions\](/concepts/compositions) and \[Data Attributes\](/concepts/data-attributes).

\## Overview

Hyperframes uses HTML as the source of truth for describing a video:

\\* \*\*HTML clips\*\* = video, image, audio, composition
\\* \*\*\[Data attributes\](/concepts/data-attributes)\*\* = timing, metadata, styling
\\* \*\*CSS\*\* = positioning and appearance
\\* \*\*GSAP timeline\*\* = animations and playback sync (see \[GSAP Animation\](/guides/gsap-animation))

\## Framework-Managed Behavior

The framework reads data attributes and automatically manages:

\\* \*\*Primitive clip timeline entries\*\* — reads \`data-start\`, \`data-duration\`, and \`data-track-index\` from clips and adds them to the GSAP timeline
\\* \*\*Media playback\*\* (play, pause, seek) for \`\` and \`\`
\\* \*\*Clip lifecycle\*\* — clips are mounted/unmounted based on \`data-start\` and \`data-duration\`
\\* \*\*Timeline synchronization\*\* — keeps media in sync with the GSAP master timeline
\\* \*\*Media loading\*\* — waits for all media to load before resolving timing

Mounting/unmounting controls \*\*presence\*\*, not appearance. Transitions (fade in, slide in) are animated in scripts.

 Do not manually call \`video.play()\`, \`video.pause()\`, set \`audio.currentTime\`, or mount/unmount clips in scripts. The framework owns media playback and clip lifecycle. See \[Common Mistakes\](/guides/common-mistakes) for more details.

\## Viewport

Every composition must include \`data-width\` and \`data-height\` on the root element:

\`\`\`html theme={null}

\`\`\`

Common sizes:

\\* \*\*Landscape\*\*: \`data-width="1920" data-height="1080"\`
\\* \*\*Portrait\*\*: \`data-width="1080" data-height="1920"\`

\## All Clip Attributes

\| Attribute \| Applies To \| Required \| Description \|
\| \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- \| \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- \| \-\-\-\-\-\-\-\-\-\-\-\-\-\-\- \| \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- \|
\| \`id\` \| All \| Yes \| Unique identifier (e.g., \`"el-1"\`). Used for relative timing references and CSS targeting. \|
\| \`class="clip"\` \| Visible elements \| Yes \| Enables runtime visibility management. Omit for audio-only clips. \|
\| \`data-start\` \| All \| Yes \| Start time in seconds (e.g., \`"0"\`, \`"5.5"\`), or a clip ID reference for \[relative timing\](#relative-timing) (e.g., \`"intro"\`). \|
\| \`data-duration\` \| video, img, audio \| See below \| Duration in seconds. \*\*Required\*\* for images. Optional for video/audio (defaults to source duration). Not used on compositions. \|
\| \`data-track-index\` \| All \| Yes \| Timeline track number. Controls z-ordering (higher = in front). Clips on the same track cannot overlap. \|
\| \`data-media-start\` \| video, audio \| No \| Playback offset / trim point in source file (seconds). Default: \`0\`. See \[Data Attributes\](/concepts/data-attributes). \|
\| \`data-volume\` \| audio, video \| No \| Volume level from \`0\` to \`1\`. Default: \`1\`. \|
\| \`data-composition-id\` \| div \| On compositions \| Unique composition ID. Must match the key used in \`window.\_\_timelines\`. \|
\| \`data-composition-src\` \| div \| No \| Path to external composition HTML file (for \[nested compositions\](#composition-clips)). \|
\| \`data-width\` \| div \| On compositions \| Composition width in pixels. \|
\| \`data-height\` \| div \| On compositions \| Composition height in pixels. \|

\## Clip Types

 Video clips embed \`\` elements with timing and playback attributes.

 \`\`\`html theme={null}

 \`\`\`

 \*\*Key behavior:\*\*

 \\* \`data-duration\` is \*\*optional\*\* — defaults to the remaining duration of the source file from \`data-media-start\`
 \\* If source media runs out before \`data-duration\`, the clip shows the last frame (freeze frame)
 \\* \`data-media-start\` trims the beginning of the source video — \`data-media-start="5"\` starts playback 5 seconds into the source file
 \\* \`data-volume\` controls the audio volume of the video — set to \`"0"\` for silent video
 \\* Do \*\*not\*\* add \`class="clip"\` to video elements — the framework manages their visibility directly


 Do not animate \`width\`, \`height\`, \`top\`, or \`left\` directly on \`\` elements with GSAP. This can cause Chrome to stop rendering video frames. Wrap the video in a \`

\` and animate the wrapper instead. See \[Common Mistakes\](/guides/common-mistakes).




Image clips display static images with controlled timing.

\`\`\`html theme={null}
![](https://hyperframes.heygen.com/reference/assets/overlay.png)
\`\`\`

\*\*Key behavior:\*\*

\\* \`data-duration\` is \*\*required\*\* for images (unlike video/audio, there is no source duration to default to)
\\* \`class="clip"\` is \*\*required\*\* — this enables the runtime to show/hide the image based on timing
\\* Supported formats: PNG, JPG, WebP, SVG, GIF (first frame only)
\\* Position and size with CSS — the image renders at its natural size unless styled otherwise

Audio clips add sound to the composition without any visual element.

\`\`\`html theme={null}

\`\`\`

\*\*Key behavior:\*\*

\\* \`data-duration\` is \*\*optional\*\* — defaults to the remaining duration of the source file from \`data-media-start\`
\\* Audio clips are invisible — do not add \`class="clip"\` (there is nothing to show/hide)
\\* \`data-volume\` controls volume — use \`"0.5"\` for background music at 50% volume
\\* \`data-media-start\` trims the beginning of the audio source, just like video
\\* Multiple audio clips can overlap on different tracks for layered sound design

Composition clips embed one composition inside another, enabling modular, reusable video building blocks.

\`\`\`html theme={null}


\`\`\`

\*\*Key behavior:\*\*

\\* Compositions do \*\*not\*\* use \`data-duration\` — duration is determined by the composition's GSAP timeline (\`tl.duration()\`)
\\* External compositions are loaded from \`data-composition-src\` and wrapped in \`
