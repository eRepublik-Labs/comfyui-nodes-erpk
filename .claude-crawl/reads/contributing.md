[Skip to main content](https://hyperframes.heygen.com/contributing#content-area)

[HyperFrames home page![light logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/light.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=8fff06fe865e474513624008576b71bb)![dark logo](https://mintcdn.com/hyperframes/f2-jlVtMPgjQyGrS/logo/dark.svg?fit=max&auto=format&n=f2-jlVtMPgjQyGrS&q=85&s=5c0e7bb1b0c720593e3f904b47b9e1a3)](https://hyperframes.heygen.com/)

Search...

⌘KAsk AI

Search...

Navigation

Contributing

Contributing

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

[Documentation](https://hyperframes.heygen.com/introduction) [Catalog](https://hyperframes.heygen.com/catalog/blocks/instagram-follow) [Packages](https://hyperframes.heygen.com/packages/core) [Reference](https://hyperframes.heygen.com/reference/html-schema)

Thanks for your interest in contributing to Hyperframes! This guide covers everything you need to get set up, run tests, and submit a pull request.

## [​](https://hyperframes.heygen.com/contributing\#getting-started)  Getting Started

1

[Navigate to header](https://hyperframes.heygen.com/contributing#)

Fork and clone

Fork the repository on GitHub, then clone your fork:

```
git clone https://github.com/YOUR_USERNAME/hyperframes.git
cd hyperframes
```

2

[Navigate to header](https://hyperframes.heygen.com/contributing#)

Install dependencies

Hyperframes uses [bun](https://bun.sh/) for package management:

```
bun install
```

3

[Navigate to header](https://hyperframes.heygen.com/contributing#)

Build all packages

Build the monorepo to ensure everything compiles:

```
bun run build
```

4

[Navigate to header](https://hyperframes.heygen.com/contributing#)

Run the studio

Start the development server to verify your setup:

```
bun run dev
```

If the studio opens at `http://localhost:3000` with a preview, your environment is ready.

5

[Navigate to header](https://hyperframes.heygen.com/contributing#)

Create a branch

Create a feature branch for your work:

```
git checkout -b my-feature
```

## [​](https://hyperframes.heygen.com/contributing\#development)  Development

### [​](https://hyperframes.heygen.com/contributing\#common-commands)  Common Commands

```
bun install                          # Install all dependencies
bun run dev                          # Start the studio (composition editor + live preview)
bun run build                        # Build all packages
bun run --filter '*' typecheck       # Type-check all packages
```

### [​](https://hyperframes.heygen.com/contributing\#running-tests)  Running Tests

Core

Engine

Runtime Contract

Producer (Docker)

```
bun run --filter @hyperframes/core test
```

### [​](https://hyperframes.heygen.com/contributing\#running-all-tests)  Running All Tests

```
bun run --filter '*' test
```

## [​](https://hyperframes.heygen.com/contributing\#packages)  Packages

| Package | Path | Description |
| --- | --- | --- |
| [`@hyperframes/core`](https://hyperframes.heygen.com/packages/core) | `packages/core` | Types, HTML generation, runtime, linter |
| [`@hyperframes/engine`](https://hyperframes.heygen.com/packages/engine) | `packages/engine` | Seekable page-to-video capture engine |
| [`@hyperframes/producer`](https://hyperframes.heygen.com/packages/producer) | `packages/producer` | Full rendering pipeline (capture + encode) |
| [`@hyperframes/studio`](https://hyperframes.heygen.com/packages/studio) | `packages/studio` | Composition editor UI |
| [`hyperframes`](https://hyperframes.heygen.com/packages/cli) | `packages/cli` | CLI for creating, previewing, and rendering |

## [​](https://hyperframes.heygen.com/contributing\#what-to-work-on)  What to Work On

Not sure where to start? Here are some ideas:

- **Good first issues** — look for issues labeled `good first issue` on GitHub
- **Documentation** — improve docs, add examples, fix typos
- **Linter rules** — add new rules to catch more composition mistakes
- **Examples** — create new starter examples
- **Bug fixes** — check the issue tracker for reported bugs

## [​](https://hyperframes.heygen.com/contributing\#pull-requests)  Pull Requests

### [​](https://hyperframes.heygen.com/contributing\#commit-format)  Commit Format

Use [conventional commit](https://www.conventionalcommits.org/) format for all commits and PR titles:

```
feat: add timeline export
fix: resolve seek overflow at composition boundary
docs: add GSAP easing examples
refactor: extract frame buffer pool into shared module
test: add regression test for nested composition timing
```

### [​](https://hyperframes.heygen.com/contributing\#ci-requirements)  CI Requirements

All of the following must pass before your PR can be merged:

- **Build** — `bun run build` succeeds
- **Type check** — `bun run --filter '*' typecheck` reports no errors
- **Tests** — all test suites pass
- **Semantic PR title** — PR title follows conventional commit format

### [​](https://hyperframes.heygen.com/contributing\#review-process)  Review Process

- PRs require at least 1 approval from a maintainer
- Keep PRs focused — one feature or fix per PR
- Include a clear description of what changed and why
- Add tests for new features and bug fixes

## [​](https://hyperframes.heygen.com/contributing\#reporting-issues)  Reporting Issues

- Use [GitHub Issues](https://github.com/heygen-com/hyperframes/issues) for bug reports and feature requests
- Search existing issues before creating a new one
- For bug reports, include:
  - Steps to reproduce
  - Expected behavior vs. actual behavior
  - Hyperframes version (`npx hyperframes info`)
  - Operating system and Node.js version

## [​](https://hyperframes.heygen.com/contributing\#community)  Community

## GitHub Issues

Report bugs, request features, and discuss ideas.

## Code of Conduct

Our community standards and expectations.

## [​](https://hyperframes.heygen.com/contributing\#license)  License

By contributing, you agree that your contributions will be licensed under the [MIT License](https://github.com/heygen-com/hyperframes/blob/main/LICENSE).

[Previous](https://hyperframes.heygen.com/reference/html-schema) [Testing Local CLI ChangesHow to test unreleased CLI changes outside the monorepo using your local build.\\
\\
Next](https://hyperframes.heygen.com/contributing/testing-local-changes)

⌘I

On this page

- [Getting Started](https://hyperframes.heygen.com/contributing#getting-started)
- [Development](https://hyperframes.heygen.com/contributing#development)
- [Common Commands](https://hyperframes.heygen.com/contributing#common-commands)
- [Running Tests](https://hyperframes.heygen.com/contributing#running-tests)
- [Running All Tests](https://hyperframes.heygen.com/contributing#running-all-tests)
- [Packages](https://hyperframes.heygen.com/contributing#packages)
- [What to Work On](https://hyperframes.heygen.com/contributing#what-to-work-on)
- [Pull Requests](https://hyperframes.heygen.com/contributing#pull-requests)
- [Commit Format](https://hyperframes.heygen.com/contributing#commit-format)
- [CI Requirements](https://hyperframes.heygen.com/contributing#ci-requirements)
- [Review Process](https://hyperframes.heygen.com/contributing#review-process)
- [Reporting Issues](https://hyperframes.heygen.com/contributing#reporting-issues)
- [Community](https://hyperframes.heygen.com/contributing#community)
- [License](https://hyperframes.heygen.com/contributing#license)

Assistant

Responses are generated using AI and may contain mistakes.
