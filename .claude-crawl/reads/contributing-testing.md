[Skip to main content](https://hyperframes.heygen.com/contributing/testing-local-changes#content-area)

[HyperFrames home page![light logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/light.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=8fff06fe865e474513624008576b71bb)![dark logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/dark.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=5c0e7bb1b0c720593e3f904b47b9e1a3)](https://hyperframes.heygen.com/)

Search...

⌘KAsk AI

Search...

Navigation

Contributing

Testing Local CLI Changes

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

When you modify the CLI or any package it bundles (core, engine, producer, studio), you need to test those changes against real projects _outside_ the monorepo — the same way an end user would run `hyperframes preview`.

## [​](https://hyperframes.heygen.com/contributing/testing-local-changes\#prerequisites)  Prerequisites

Build the monorepo first. Every time you change source files, rebuild before testing.

```
# From the monorepo root
bun run build
```

## [​](https://hyperframes.heygen.com/contributing/testing-local-changes\#option-1-bun-link-recommended)  Option 1: bun link (recommended)

`bun link` makes the `hyperframes` binary in your `$PATH` point at your local build. It survives across terminal sessions and auto-picks up new builds without re-linking.

```
# If you previously installed hyperframes globally, remove it first —
# a global install takes priority over bun link and shadows your local build.
npm uninstall -g hyperframes 2>/dev/null

# Link your local build
cd packages/cli
bun link

# Verify — should print your local version AND point to the monorepo
hyperframes --version
which hyperframes
```

Now use `hyperframes` normally in any directory:

```
cd ~/my-video-project
hyperframes preview .
```

**After every `bun run build`** the linked binary is already up to date — no re-linking needed.To restore the published release when you’re done:

```
bun unlink hyperframes
npm install -g hyperframes@latest
```

## [​](https://hyperframes.heygen.com/contributing/testing-local-changes\#option-2-node-alias-no-path-changes)  Option 2: node alias (no PATH changes)

If you don’t want to touch your global `$PATH`, add a shell alias or call `node` directly:

```
# Temporary alias for your current shell session
alias hyperframes="node /path/to/hyperframes/packages/cli/dist/cli.js"

# Or invoke directly
node /path/to/hyperframes/packages/cli/dist/cli.js preview .
```

Replace `/path/to/hyperframes` with your actual monorepo path.

## [​](https://hyperframes.heygen.com/contributing/testing-local-changes\#option-3-npm-pack-test-the-exact-published-artifact)  Option 3: npm pack (test the exact published artifact)

Use this when you want to verify what would actually ship in a release, including the bundled studio and examples.

```
cd packages/cli
npm pack
# Creates: hyperframes-<version>.tgz

# Test it in an isolated directory
mkdir /tmp/pack-test && cd /tmp/pack-test
npx /path/to/hyperframes/packages/cli/hyperframes-<version>.tgz init my-video
cd my-video
npx /path/to/hyperframes/packages/cli/hyperframes-<version>.tgz preview .
```

## [​](https://hyperframes.heygen.com/contributing/testing-local-changes\#testing-the-fix-branches)  Testing the fix branches

When validating a specific bug fix, extract one of the test project archives and run through the scenario:

```
# Example: testing audio-after-seek fix
unzip golden-lyric-video.zip && cd golden-lyric-video
hyperframes preview .
# 1. Press Play — confirm audio plays
# 2. Drag the timeline scrubber to a different position
# 3. Press Play again — audio should resume from the seeked position
```

Common test scenarios:

| Bug | Project | Steps |
| --- | --- | --- |
| Audio silent after seek | `golden-lyric-video` | Play → seek → play again, verify audio |
| Render stuck at 0% | any | Renders tab → Export → watch progress bar |
| Download 404 after restart | any | Complete a render → `Ctrl+C` → restart → Download |
| Timeline stops early | `intro-vid` | Play → should reach `0:05`, not stop at `0:03` |
| Lottie missing | `hyperframe-build-up-demo` | Play → rocket visible during 0–2 s |
| Blank thumbnails | any | Compositions sidebar should show previews |

## [​](https://hyperframes.heygen.com/contributing/testing-local-changes\#troubleshooting)  Troubleshooting

**Changes not reflected after `bun run build`**The CLI binary is a single bundled file at `packages/cli/dist/cli.js`. If your change is in `@hyperframes/core` or another workspace package, make sure `bun run build` rebuilt _all_ packages — the CLI bundles its dependencies at build time.**`hyperframes` still shows the old version / old UI**A globally installed `hyperframes` package shadows `bun link`. Check which binary is active:

```
which hyperframes
```

If it points to a global store rather than your monorepo, remove the global install and re-link:

```
npm uninstall -g hyperframes
cd packages/cli && bun link
```

**Port already in use**`hyperframes preview` defaults to port 3002 and auto-increments if it’s taken. Pass `--port` to use a specific port:

```
hyperframes preview . --port 4000
```

[Previous\\
\\
ContributingHow to contribute to Hyperframes.](https://hyperframes.heygen.com/contributing)

⌘I

On this page

- [Prerequisites](https://hyperframes.heygen.com/contributing/testing-local-changes#prerequisites)
- [Option 1: bun link (recommended)](https://hyperframes.heygen.com/contributing/testing-local-changes#option-1-bun-link-recommended)
- [Option 2: node alias (no PATH changes)](https://hyperframes.heygen.com/contributing/testing-local-changes#option-2-node-alias-no-path-changes)
- [Option 3: npm pack (test the exact published artifact)](https://hyperframes.heygen.com/contributing/testing-local-changes#option-3-npm-pack-test-the-exact-published-artifact)
- [Testing the fix branches](https://hyperframes.heygen.com/contributing/testing-local-changes#testing-the-fix-branches)
- [Troubleshooting](https://hyperframes.heygen.com/contributing/testing-local-changes#troubleshooting)

Assistant

Responses are generated using AI and may contain mistakes.
