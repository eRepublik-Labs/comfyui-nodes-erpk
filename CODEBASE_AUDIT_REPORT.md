# ComfyUI Custom Nodes ERPK Codebase Audit

Date: 2026-05-14

Scope: static/manual code review plus local test and security-tool runs. The review focused on security risks, dependency hygiene, CI gaps, and maintainability improvements. No source code was changed as part of the audit, other than creating this report.

## Repository State

Before tool runs, the worktree already had uncommitted changes in:

- `settings.py`
- `tests/test_settings.py`

Those were treated as existing user work.

## Executive Summary

The codebase is a Python ComfyUI custom-node package with provider integrations for WaveSpeed, Claude, Gemini, OpenAI, Apple SHARP, utility nodes, and browser-side ComfyUI extensions.

The highest-priority risks are:

1. Shared workflow API routes allow broad read/write/delete operations without owner/admin authorization.
2. Several server-side helpers fetch user-provided URLs without host restrictions, byte limits, or private-network protections.
3. Multi-user API-key resolution can still cross user boundaries when the current user cannot be resolved.
4. The client-ID registration route trusts caller-supplied `client_id`.
5. CI does not currently run tests or security scans.

## Security Findings

### High: Shared Workflow Routes Lack Authorization

Files:

- `__init__.py`
- `shared_workflows.py`

Routes:

- `GET /erpk/shared_workflows`
- `GET /erpk/shared_workflows/{name}`
- `POST /erpk/shared_workflows`
- `DELETE /erpk/shared_workflows/{name}`

Relevant code:

- `__init__.py:134`
- `__init__.py:141`
- `__init__.py:154`
- `__init__.py:175`
- `shared_workflows.py:105`
- `shared_workflows.py:151`

Issue:

The API records `created_by` and `modified_by`, but does not enforce owner/admin permissions on overwrite, read, or delete. In a multi-user ComfyUI deployment with untrusted users, any user who can call these routes can overwrite or delete another user's shared workflows.

Recommended remediation:

- Define the intended sharing model explicitly: global public library, owner-only edits, admin-only deletes, etc.
- Enforce authorization server-side before save/delete.
- Return `403` for unauthorized changes.
- Consider including immutable `created_by_user_id` in addition to display names.
- Add tests covering unauthorized overwrite/delete.

### High: Server-Side URL Fetching Creates SSRF and DoS Risk

Files:

- `utils/preview_anything.py`
- `wavespeed/nodes.py`
- `wavespeed/wavespeed_api/utils.py`

Relevant code:

- `utils/preview_anything.py:221`
- `utils/preview_anything.py:232`
- `utils/preview_anything.py:246`
- `wavespeed/nodes.py:162`
- `wavespeed/nodes.py:229`
- `wavespeed/wavespeed_api/utils.py:32`
- `wavespeed/wavespeed_api/utils.py:72`

Issue:

Several paths fetch user-provided URLs server-side and read entire responses into memory. This can be abused for:

- SSRF to internal services or metadata endpoints.
- Private-network probing.
- Large-response memory exhaustion.
- Image decompression bombs.
- Unexpected redirects to private hosts.

Bandit also flagged `urllib.request.urlopen` in `utils/preview_anything.py` as medium severity.

Recommended remediation:

- Allow only `http` and `https` where remote fetches are truly needed.
- Resolve and block private, loopback, link-local, multicast, and reserved IP ranges.
- Re-check resolved host after redirects.
- Stream responses with a maximum byte budget.
- Validate content type and extension against expected media type.
- Set PIL `Image.MAX_IMAGE_PIXELS` or equivalent safeguards.
- Consider allowing only known provider domains for WaveSpeed media outputs.

### Medium: Multi-User Settings Fallback Can Leak API Keys

File:

- `settings.py`

Relevant code:

- `settings.py:72`
- `settings.py:82`
- `settings.py:97`

Issue:

The current identified-user path is strict, which is good. However, if no `user_id` is resolved, `get_comfy_setting()` scans all user directories and returns the first matching value, preferring `default`. In multi-user mode, a missing WebSocket/client mapping could cause a user to use another user's API key.

Recommended remediation:

- In multi-user mode, return the default unless a user is known.
- Keep directory scanning only for explicit single-user mode.
- Add tests for "multi-user enabled but current user unresolved".

### Medium: `/erpk/register_user` Trusts Caller-Supplied `client_id`

File:

- `__init__.py`

Relevant code:

- `__init__.py:95`
- `__init__.py:99`
- `__init__.py:103`

Issue:

The route maps a posted `client_id` to the request user. There is no proof that the requester owns that WebSocket client ID. If a client ID can be guessed or exposed, a user can poison the map.

Recommended remediation:

- Validate client ownership server-side if ComfyUI exposes a reliable mapping.
- Add TTL cleanup for stale entries.
- Add a lock around `_client_user_map`.
- Consider avoiding client-provided IDs entirely if a server-side execution context can expose the user.

### Medium: GitHub Actions Manual Input Shell Injection Risk

File:

- `.github/workflows/update-changelog.yml`

Relevant code:

- `.github/workflows/update-changelog.yml:29`
- `.github/workflows/update-changelog.yml:30`

Issue:

The manual `workflow_dispatch` input is interpolated directly into shell code. This is scoped to users who can manually trigger the workflow, but it is still better to avoid direct expression interpolation inside `run` scripts.

Recommended remediation:

- Pass workflow inputs through `env:`.
- Use shell variables with normal quoting.
- Validate version input against a strict pattern before use.

## Maintainability and Quality Findings

### Dependency Metadata Is Inconsistent

Files:

- `pyproject.toml`
- `requirements.txt`

Relevant code:

- `pyproject.toml:9`
- `requirements.txt:4`
- `requirements.txt:20`

Issue:

`pyproject.toml` and `requirements.txt` specify different minimum versions. `requirements.txt` also includes an unpinned Git dependency:

```text
sharp @ git+https://github.com/apple/ml-sharp.git
```

Recommended remediation:

- Choose a single source of truth for runtime dependencies.
- Align versions between files.
- Pin Git dependencies to a tag or commit hash.
- Add a dependency audit workflow.

### Global Monkey Patches Need Idempotence Guards

Files:

- `metadata_filter.py`
- `history_cleaner.py`

Relevant code:

- `metadata_filter.py:38`
- `metadata_filter.py:42`
- `history_cleaner.py:49`
- `history_cleaner.py:57`

Issue:

These modules patch global ComfyUI methods at import time. If modules reload, patches may be wrapped multiple times.

Recommended remediation:

- Add sentinel attributes such as `_erpk_patched = True`.
- Avoid double wrapping.
- Prefer relative import for `get_comfy_setting` in `history_cleaner.py` if package import context allows it.

### CI Does Not Run Tests or Security Checks

Files:

- `.github/workflows/publish.yml`
- `.github/workflows/update-changelog.yml`

Issue:

The repository has publishing/changelog workflows, but no PR/branch CI that runs tests, linting, or security scans.

Recommended remediation:

- Add a CI workflow for pull requests and pushes.
- Run `pytest`.
- Run `bandit`.
- Run `pip-audit`.
- Consider `ruff` and type checks if appropriate.

## Positive Observations

### Shared Workflow Filename Validation Is Good

File:

- `shared_workflows.py`

Relevant code:

- `shared_workflows.py:21`
- `shared_workflows.py:25`
- `shared_workflows.py:38`

The filename whitelist and realpath containment check reduce path traversal risk.

### Frontend Markdown Rendering Avoids Direct HTML Injection

File:

- `web/preview_anything.js`

Relevant code:

- `web/preview_anything.js:148`
- `web/preview_anything.js:252`
- `web/preview_anything.js:276`

The markdown renderer builds DOM nodes with `textContent` rather than `innerHTML`, and link URLs are scheme-filtered.

## Tool Results

### Pytest

Command:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider
```

Result:

```text
1755 passed, 5 failed
```

Failures:

```text
FAILED tests/test_gemini_image_edit_additional_images.py::test_input_types_has_additional_images
FAILED tests/test_gemini_image_edit_additional_images.py::test_edit_image_accepts_additional_images_kwarg
FAILED tests/test_gemini_image_edit_additional_images.py::test_additional_images_merged_into_contents
FAILED tests/test_v3_gemini_nodes.py::TestGeminiV3Compliance::test_schema_has_inputs[GeminiAPIConfig]
FAILED tests/test_v3_gemini_nodes.py::TestGeminiCustomTypes::test_veo_text_to_video_accepts_required_client
```

Interpretation:

- `tests/test_gemini_image_edit_additional_images.py` expects old-style `GeminiImageEdit.INPUT_TYPES` and `GeminiImageEdit.edit_image`.
- Current V3 `GeminiImageEdit` does not expose those members.
- `GeminiAPIConfig` currently defines a schema with no inputs, while the V3 compliance test expects at least one input.
- `VeoTextToVideo` marks `client` optional, while the test expects it to be required.

Recommended next step:

Decide whether the tests are stale or the V3 nodes need compatibility shims. If old V1-style entry points are intentionally removed, update the tests. If backward compatibility is required, add thin compatibility methods around the V3 execution path.

### Bandit

Command:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m bandit -q -r __init__.py settings.py shared_workflows.py metadata_filter.py history_cleaner.py openai claude gemini wavespeed utils apple
```

Result:

```text
Total issues: 8
High: 0
Medium: 2
Low: 6
```

Medium findings:

```text
B310 urllib urlopen
utils/preview_anything.py:232
utils/preview_anything.py:246
```

Low findings:

```text
B110 try/except/pass
history_cleaner.py:41
gemini/veo_nodes.py:448
gemini/veo_nodes.py:705
wavespeed/wavespeed_api/client.py:109
wavespeed/wavespeed_api/client.py:167

B112 try/except/continue
utils/preview_anything.py:455
```

Interpretation:

Bandit confirms the URL-fetching path is the primary scanner-visible security issue. The low-severity exception findings are mostly error-handling hygiene issues, but they can hide operational failures.

### pip-audit

Installed packages:

- `torch 2.12.0`
- `bandit 1.9.4`
- `pip-audit 2.10.0`

Requirements-file mode command:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m pip_audit -r requirements.txt --cache-dir /private/tmp/pip-audit-cache
```

Result:

The requirements-file audit could not complete because pip-audit's temporary resolver virtual environment crashed during `ensurepip`:

```text
subprocess.CalledProcessError: Command '['.../bin/python', '-m', 'ensurepip', '--upgrade', '--default-pip']' died with <Signals.SIGABRT: 6>
```

Installed-environment audit command:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m pip_audit --cache-dir /private/tmp/pip-audit-cache --progress-spinner off
```

Result:

```text
Found 29 known vulnerabilities in 11 packages
```

Reported packages:

| Package | Version | Vulnerabilities | Fix Version |
| --- | ---: | --- | --- |
| aiohttp | 3.13.3 | CVE-2026-34515, CVE-2026-34513, CVE-2026-34516, CVE-2026-34517, CVE-2026-34519, CVE-2026-34518, CVE-2026-34520, CVE-2026-34525, CVE-2026-22815, CVE-2026-34514 | 3.13.4 |
| cryptography | 46.0.5 | CVE-2026-34073, CVE-2026-39892 | 46.0.7 |
| Pillow | 12.1.1 | CVE-2026-40192, CVE-2026-42308, CVE-2026-42309, CVE-2026-42310, CVE-2026-42311 | 12.2.0 |
| pip | 26.0.1 | CVE-2026-3219, CVE-2026-6357 | 26.1 for CVE-2026-6357 |
| pyasn1 | 0.6.2 | CVE-2026-30922 | 0.6.3 |
| pygments | 2.19.2 | CVE-2026-4539 | 2.20.0 |
| pytest | 9.0.2 | CVE-2025-71176 | 9.0.3 |
| python-multipart | 0.0.22 | CVE-2026-40347, CVE-2026-42561 | 0.0.27 |
| rembg | 2.0.73 | CVE-2026-40086, GHSA-55v6-g8pm-pw4c | 2.0.75 |
| requests | 2.32.5 | CVE-2026-25645 | 2.33.0 |
| urllib3 | 2.6.3 | CVE-2026-44431, CVE-2026-44432 | 2.7.0 |

Important caveat:

The installed-environment audit warned that it was auditing:

```text
/Users/alex.geana/.local/share/mise/installs/python/3.11.14/bin/python
```

while a virtual environment exists at:

```text
/Users/alex.geana/GitHub/ComfyUI-Custom-Nodes/.venv
```

So this audit is useful for the active Python used by the commands, but it is not a clean resolved audit of `requirements.txt`.

Recommended next step:

- Fix the requirements-file audit environment so `pip-audit -r requirements.txt` can complete.
- Then update direct minimum versions in `pyproject.toml` and `requirements.txt`.
- For transitive vulnerabilities, update the parent packages or lockfile.

## Prioritized Remediation Plan

1. Add authorization policy to shared workflow routes.
2. Harden all server-side URL fetches with host restrictions, redirect checks, streaming, and byte limits.
3. Tighten multi-user API-key lookup so unresolved users do not fall back to peer directory scanning in multi-user mode.
4. Validate or remove trust in caller-provided `client_id` registration.
5. Resolve the 5 pytest failures by deciding whether tests or Gemini V3 compatibility should change.
6. Add CI with pytest, Bandit, and pip-audit.
7. Align dependency metadata and pin the SHARP Git dependency.
8. Add idempotence guards to monkey patches.

## Commands Run

```sh
python -m pip install torch bandit pip-audit
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 python -m bandit -q -r __init__.py settings.py shared_workflows.py metadata_filter.py history_cleaner.py openai claude gemini wavespeed utils apple
PYTHONDONTWRITEBYTECODE=1 python -m pip_audit -r requirements.txt --cache-dir /private/tmp/pip-audit-cache
PYTHONDONTWRITEBYTECODE=1 python -m pip_audit --cache-dir /private/tmp/pip-audit-cache --progress-spinner off
```
