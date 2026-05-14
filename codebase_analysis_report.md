# ComfyUI ERPK Nodes: Codebase Analysis & Security Report
*Date: May 14, 2026*

## 🛡️ Security Vulnerabilities

### 1. Server-Side Request Forgery (SSRF)
*   **Affected Files:** `utils/preview_anything.py`, `wavespeed/nodes.py`
*   **Issue:** The `PreviewAnything`, `PreviewVideo`, and `SaveAudio` nodes fetch data from arbitrary URLs. `PreviewAnything` specifically allows loopback requests to `127.0.0.1:8188`.
*   **Risk:** A malicious workflow could be used to probe the local network or query ComfyUI's internal APIs, potentially leaking data or triggering unauthorized server-side actions.

### 2. Path Injection / Directory Traversal
*   **Affected Files:** `apple/sharp_nodes.py`, `wavespeed/nodes.py`, `utils/preview_anything.py`
*   **Issue:** User-provided string prefixes (e.g., `save_file_prefix`, `filename_prefix`) are used in `os.path.join` without strict sanitization.
*   **Risk:** A malicious user could provide a prefix like `../../` to write files outside of the designated `output` or `temp` directories, potentially overwriting critical system or application files.

### 3. Lack of Authorization in Shared Workflows
*   **Affected Files:** `__init__.py`, `shared_workflows.py`
*   **Issue:** The `/erpk/shared_workflows` API allows any user to delete any workflow via a `DELETE` request.
*   **Risk:** In a multi-user environment, there are no ownership checks. One user can delete another's shared workflow, leading to data loss and disruption.

### 4. Setting Leakage via Default Fallback
*   **Affected Files:** `settings.py`
*   **Issue:** If a setting is not found for a specific `user_id`, the system scans the "default" user directory.
*   **Risk:** This could inadvertently leak a global or "default" API key to a specific user who was not intended to have access to it, violating user isolation.

### 5. Plaintext Secrets
*   **Affected Files:** `comfy.settings.json` (indirectly), workflow JSONs.
*   **Issue:** API keys are stored in plaintext in the ComfyUI settings file and embedded in saved workflow JSON files.
*   **Risk:** If a workflow file is shared or the server's storage is compromised, all configured API keys are immediately exposed.

---

## 🚀 Recommended Improvements

### 1. Media Handling & Performance
*   **Vision API Payloads:** Switch from PNG to **JPEG or WebP** in `claude/vision_analysis.py`, `gemini/nodes.py`, and `openai/nodes.py`. This would significantly reduce bandwidth and latency for multimodal API calls.
*   **Centralized Utilities:** Move media download, tensor conversion, and path sanitization into a unified `utils/media.py` to ensure consistent security checks across all provider nodes.

### 2. Architectural Refinement
*   **Settings Caching:** Add a simple in-memory cache to `settings.py` to prevent redundant disk I/O when multiple nodes in a graph request the same API keys.
*   **Dynamic Model Discovery:** Instead of hardcoding model lists in `IO.Combo.Input`, implement a mechanism to fetch available models from the providers or a remote configuration file.
*   **History Cleaner Efficiency:** Refactor `history_cleaner.py` to use a single background worker thread and a queue, rather than spawning a new thread for every individual task completion.

### 3. Frontend / UI
*   **Enhanced Sanitization:** Move the path-safe name validation in `shared_workflows.js` to a more robust implementation that mirrors the server-side logic.
