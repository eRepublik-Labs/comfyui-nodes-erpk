// ABOUTME: Registers ERPK settings in ComfyUI Settings UI, with API keys saved to the server's key store
// ABOUTME: Handles multi-user client registration and disables api_key widgets a stored key overrides

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";
import { writeRequest } from "./write_request.js";

// API keys live in the server's per-user key store behind /erpk/keys. They are
// never ComfyUI settings: ComfyUI serves comfy.settings.json to every user.
//
// ComfyUI Settings UI renders these in REVERSE order of registration:
// array[0] → bottom of the panel, array[n-1] → top. To control where a key
// appears in the rendered list, place it accordingly in this array.
// tryInjectBanner anchors on the "Anthropic API Key" and "WaveSpeed API Key" names.
const API_KEY_PROVIDERS = [
    { provider: "byteplus", name: "BytePlus ModelArk API Key", nodes: ["BytePlusAPIClient"] },
    { provider: "xai", name: "xAI (Grok) API Key", nodes: ["GrokAPIClient"] },
    { provider: "anthropic", name: "Anthropic API Key", nodes: ["ClaudeAPIClient"] },
    { provider: "google", name: "Google API Key", nodes: [] },
    { provider: "openai", name: "OpenAI API Key", nodes: [] },
    { provider: "wavespeed", name: "WaveSpeed API Key", nodes: ["WaveSpeedAIAPIClient"] },
];

// Lookup: node comfyClass -> provider whose stored key replaces its api_key widget
const NODE_TO_PROVIDER = {};
for (const entry of API_KEY_PROVIDERS) {
    for (const node of entry.nodes) {
        NODE_TO_PROVIDER[node] = entry.provider;
    }
}

// provider -> { set, last4 } for this user, from /erpk/keys. null until a fetch succeeds.
let keyStatus = null;

async function fetchKeyStatus() {
    try {
        const resp = await api.fetchApi("/erpk/keys");
        if (resp.ok) {
            keyStatus = await resp.json();
            lockApiKeyWidgetsInGraph();
        } else {
            console.warn(`[ERPK] API key status request failed: ${resp.status}`);
        }
    } catch (e) {
        console.warn("[ERPK] API key status request failed", e);
    }
}

// Disable the api_key widget of a node whose provider has a stored key: the
// stored key takes priority, so a key typed there would only be exposed.
function lockApiKeyWidget(node) {
    const provider = NODE_TO_PROVIDER[node.comfyClass];
    if (!provider || !keyStatus) return null;
    const widget = node.widgets?.find((w) => w.name === "api_key");
    if (!widget) return null;
    widget.disabled = keyStatus[provider]?.set === true;
    return widget;
}

function lockApiKeyWidgetsInGraph() {
    for (const node of app.graph?.nodes ?? []) {
        lockApiKeyWidget(node);
    }
}

function describeKey(status) {
    if (!status) return "Status unavailable";
    if (!status.set) return "Not set";
    return status.last4 ? `Set ••••${status.last4}` : "Set";
}

const KEY_CONTROL_CSS =
    "padding:6px 12px;border:1px solid var(--border-color,#3a3a3a);border-radius:6px;" +
    "background:var(--comfy-input-bg,#0d0d12);color:var(--input-text,#ddd);font-size:12px;" +
    "box-sizing:border-box;min-height:32px;";

// One provider's row: status, a write-only key input, Save and Clear. The key
// typed here goes to POST /erpk/keys and is never read back.
function renderKeyRow(entry) {
    const row = document.createElement("div");
    row.style.cssText = "display:flex;flex-wrap:wrap;align-items:center;gap:8px;max-width:520px;";

    const state = document.createElement("span");
    state.setAttribute("aria-live", "polite");
    state.style.cssText =
        "min-width:96px;font-size:12px;" +
        "font-family:var(--font-family-monospace,ui-monospace,Menlo,monospace);";

    const input = document.createElement("input");
    input.type = "password";
    input.autocomplete = "new-password";
    input.spellcheck = false;
    input.placeholder = "Paste a new key";
    input.setAttribute("aria-label", `New ${entry.name}`);
    input.style.cssText = KEY_CONTROL_CSS + "flex:1 1 180px;min-width:0;font-family:var(--font-family-monospace,ui-monospace,Menlo,monospace);";

    const save = document.createElement("button");
    save.type = "button";
    save.textContent = "Save";
    save.style.cssText = KEY_CONTROL_CSS + "cursor:pointer;";

    const clear = document.createElement("button");
    clear.type = "button";
    clear.textContent = "Clear";
    clear.style.cssText = KEY_CONTROL_CSS + "cursor:pointer;";

    const error = document.createElement("span");
    error.setAttribute("role", "alert");
    error.style.cssText = "flex-basis:100%;font-size:12px;color:var(--error-text,#f87171);";

    const paint = () => {
        const status = keyStatus?.[entry.provider];
        state.textContent = describeKey(status);
        state.style.opacity = status?.set ? "1" : "0.6";
        save.disabled = !input.value.trim();
        clear.disabled = status?.set !== true;
    };

    // key: the new key, or null to clear it
    const submit = async (key) => {
        save.disabled = true;
        clear.disabled = true;
        error.textContent = "";
        try {
            const resp = await writeRequest("/erpk/keys", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ provider: entry.provider, key }),
            });
            const body = await resp.json().catch(() => ({}));
            if (!resp.ok) {
                error.textContent = body.error ?? `Request failed: ${resp.status}`;
                return;
            }
            keyStatus = body;
            input.value = "";
            lockApiKeyWidgetsInGraph();
        } catch (e) {
            error.textContent = `Request failed: ${e.message}`;
        } finally {
            paint();
        }
    };

    save.addEventListener("click", () => submit(input.value.trim()));
    clear.addEventListener("click", () => submit(null));
    input.addEventListener("input", paint);
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && input.value.trim()) submit(input.value.trim());
    });

    row.append(state, input, save, clear, error);
    paint();
    return row;
}

async function registerUserContext() {
    // Register this client's user mapping for multi-user settings resolution.
    // api.fetchApi automatically adds the Comfy-User header in multi-user mode.
    try {
        await api.fetchApi("/erpk/register_user", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ client_id: api.clientId }),
        });
    } catch (e) {
        // Non-fatal: single-user mode works without this
    }
}

async function fetchUserInfo() {
    // Fetch current user info for settings display
    try {
        const resp = await api.fetchApi("/erpk/user_info");
        if (resp.ok) {
            return await resp.json();
        }
    } catch (e) {
        // Non-fatal
    }
    return { multi_user: false, user_id: "default", display_name: "default" };
}

async function fetchVersion() {
    // Fetch the ERPK package version (read from pyproject.toml server-side).
    try {
        const resp = await api.fetchApi("/erpk/version");
        if (resp.ok) {
            const data = await resp.json();
            return data.version || null;
        }
    } catch (e) {
        // Non-fatal
    }
    return null;
}

const BANNER_ID = "erpk-user-banner";

function createUserBanner(displayName, version) {
    const banner = document.createElement("div");
    banner.id = BANNER_ID;
    banner.style.cssText =
        "display:flex;align-items:center;gap:10px;padding:10px 14px;" +
        "background:rgba(79,143,247,0.06);color:#8bb4f7;" +
        "border:1px solid rgba(79,143,247,0.12);border-left:3px solid #4f8ff7;" +
        "border-radius:8px;font-size:13px;font-weight:400;margin-bottom:12px;" +
        "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;";

    const label = document.createElement("span");
    label.textContent = "Signed in as ";
    label.style.opacity = "0.7";

    const name = document.createElement("span");
    name.textContent = displayName;
    name.style.fontWeight = "600";

    banner.appendChild(label);
    banner.appendChild(name);

    if (version) {
        const ver = document.createElement("span");
        ver.textContent = `v${version}`;
        ver.title = "ERPK Custom Nodes version";
        ver.style.cssText =
            "margin-left:auto;opacity:0.6;font-size:11px;" +
            "font-family:var(--font-family-monospace,ui-monospace,Menlo,monospace);";
        banner.appendChild(ver);
    }
    return banner;
}

function tryInjectBanner(displayName, version) {
    if (document.getElementById(BANNER_ID)) return;

    // Find ERPK settings by looking for our setting labels in the dialog
    const allText = document.querySelectorAll(
        ".p-dialog-content span, .p-dialog-content label, " +
            ".comfy-modal-content span, .comfy-modal-content label"
    );
    let firstLabel = null;
    let lastLabel = null;
    for (const el of allText) {
        const text = el.textContent.trim();
        if (text === "Anthropic API Key" && !firstLabel) firstLabel = el;
        if (text === "WaveSpeed API Key") lastLabel = el;
    }
    if (!firstLabel || !lastLabel) return;

    // Find the lowest common ancestor of first and last ERPK settings —
    // this is the settings content container, not the full dialog wrapper
    const ancestors = new Set();
    let node = firstLabel;
    while (node) {
        ancestors.add(node);
        node = node.parentElement;
    }
    let container = lastLabel;
    while (container) {
        if (ancestors.has(container)) break;
        container = container.parentElement;
    }
    if (!container) return;

    container.prepend(createUserBanner(displayName, version));
}

function observeSettingsDialog(displayName, version) {
    // Watch for dialog open/close to inject the banner.
    const observer = new MutationObserver(() => {
        const dialogOpen =
            document.querySelector(".p-dialog-content") ||
            document.querySelector(".comfy-modal-content");
        if (dialogOpen) {
            tryInjectBanner(displayName, version);
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });
}

// Slider onChange fires per detent during a drag, so 1 → 5 produces 4 fires.
// We debounce (wait for the slider to settle) AND dedupe (skip if value
// matches the previous notification), and `_readyToNotify` suppresses the
// load-time onChange fire so opening Settings doesn't pop a toast.
let _lastParallelWorkersNotified = null;
let _readyToNotify = false;
let _parallelWorkersDebounce = null;
const _PARALLEL_WORKERS_DEBOUNCE_MS = 750;

function _showErpkNotice({ severity, summary, detail }) {
    try {
        if (app?.extensionManager?.toast?.add) {
            app.extensionManager.toast.add({
                severity,
                summary,
                detail,
                life: 10000,
            });
            return;
        }
    } catch (e) {
        // fall through
    }
    // Fallback: console + alert (intentionally loud, since the user
    // needs to know about restart/GPU risk)
    if (severity === "warn" || severity === "error") {
        console.warn(`[ERPK] ${summary}: ${detail}`);
    } else {
        console.info(`[ERPK] ${summary}: ${detail}`);
    }
    try { alert(`[ERPK] ${summary}\n\n${detail}`); } catch (e) {}
}

function _fireParallelWorkersNotice(n) {
    if (n === _lastParallelWorkersNotified) {
        return;
    }
    _lastParallelWorkersNotified = n;

    if (n > 1) {
        _showErpkNotice({
            severity: "warn",
            summary: "Restart ComfyUI to apply parallel workers",
            detail: "Local-diffusion workflows will race on GPU memory under multi-worker mode. Only enable this when your queue is API-only (Wavespeed / Claude / OpenAI / Gemini).",
        });
    } else {
        _showErpkNotice({
            severity: "info",
            summary: "Restart ComfyUI to apply parallel workers",
            detail: "Worker thread count change takes effect at package load.",
        });
    }
}

function onParallelWorkersChange(newValue) {
    const n = Number(newValue);
    if (!Number.isFinite(n)) {
        return;
    }
    // Suppress the load-time fire: record the value so a later real change
    // can compare against it correctly, but don't show a toast yet.
    if (!_readyToNotify) {
        _lastParallelWorkersNotified = n;
        return;
    }
    // Debounce: a slider drag fires onChange at every detent passed. Wait
    // for the slider to settle before firing the notice with the final value.
    if (_parallelWorkersDebounce !== null) {
        clearTimeout(_parallelWorkersDebounce);
    }
    _parallelWorkersDebounce = setTimeout(() => {
        _parallelWorkersDebounce = null;
        _fireParallelWorkersNotice(n);
    }, _PARALLEL_WORKERS_DEBOUNCE_MS);
}

const GENERAL_SETTINGS = [
    {
        id: "ERPK.AUTO_CLEAR_HISTORY",
        name: "Auto-Clear Job History",
        type: "boolean",
        defaultValue: false,
        category: ["ERPK", "General", "Auto-Clear Job History"],
        tooltip: "Automatically remove completed jobs from history. Reduces UI slowdown with large workflows.",
    },
    {
        id: "ERPK.PARALLEL_WORKERS",
        name: "Parallel Prompt Workers",
        type: "slider",
        defaultValue: 1,
        attrs: { min: 1, max: 8, step: 1 },
        category: ["ERPK", "General", "Parallel Prompt Workers"],
        tooltip: "Number of concurrent prompts the queue runs. 1 = ComfyUI default (serial). Higher = multiple queued prompts execute in parallel. WARNING: local-diffusion workflows will race on GPU memory — only raise this when running API-only workflows. Requires ComfyUI restart to take effect.",
        onChange: onParallelWorkersChange,
    },
    {
        id: "ERPK.GEMINI_TIMEOUT_MS",
        name: "Gemini Request Timeout (ms)",
        type: "number",
        defaultValue: 300000,
        category: ["ERPK", "General", "Gemini Request Timeout (ms)"],
        tooltip: "Per-request HTTP timeout for Gemini calls, in milliseconds. Raise for very long video jobs. Default 300000 (5 min).",
    },
];

function buildSettings() {
    const apiKeySettings = API_KEY_PROVIDERS.map((entry) => ({
        // A render function instead of "text": the frontend writes a setting to
        // comfy.settings.json only when its setter is called, and renderKeyRow
        // never calls it. The id holds no value.
        id: `ERPK.ApiKeyStore.${entry.provider}`,
        name: entry.name,
        type: () => renderKeyRow(entry),
        defaultValue: "",
        category: ["ERPK", "API Keys", entry.name],
        tooltip: `${entry.name}, saved privately for your ComfyUI user on the server. Only its last four characters are ever shown. When it is not set, the key on the node or in config.ini is used.`,
    }));
    return [...apiKeySettings, ...GENERAL_SETTINGS];
}

app.registerExtension({
    name: "ERPK.Settings",

    settings: buildSettings(),

    // init runs before the saved workflow is restored, so nodeCreated sees the status.
    async init() {
        await fetchKeyStatus();
    },

    async setup() {
        // Open the notification window 2s after setup. Any onChange fires
        // before this point are treated as initial-load seeding and don't
        // pop a toast (see onParallelWorkersChange).
        setTimeout(() => { _readyToNotify = true; }, 2000);

        // Register user context for multi-user settings resolution
        await registerUserContext();

        // Re-register on WebSocket reconnect (client_id may change)
        api.addEventListener("reconnected", () => {
            registerUserContext();
        });

        // Inject user banner (with package version) into ERPK Settings panel when dialog opens
        const userInfo = await fetchUserInfo();
        const version = await fetchVersion();
        if (version) {
            console.info(`[ERPK] Custom Nodes v${version}`);
        }
        if (userInfo.display_name) {
            observeSettingsDialog(userInfo.display_name, version);
        }
    },

    afterConfigureGraph() {
        lockApiKeyWidgetsInGraph();
    },

    nodeCreated(node) {
        const widget = lockApiKeyWidget(node);
        if (widget?.disabled) {
            widget.value = "";
        }
    },
});
