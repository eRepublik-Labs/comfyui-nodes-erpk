// ABOUTME: Registers ERPK settings (API keys, general toggles) in ComfyUI Settings UI
// ABOUTME: Handles multi-user client registration and read-only api_key widgets

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const API_KEY_SETTINGS = [
    {
        id: "ERPK.ANTHROPIC_API_KEY",
        name: "Anthropic API Key",
        nodes: ["ClaudeAPIClient"],
    },
    {
        id: "ERPK.GOOGLE_API_KEY",
        name: "Google API Key",
        nodes: ["GeminiAPIConfig", "GeminiImageGeneration", "GeminiImageEdit"],
    },
    {
        id: "ERPK.OPENAI_API_KEY",
        name: "OpenAI API Key",
        nodes: ["OpenAIAPIConfig"],
    },
    {
        id: "ERPK.WAVESPEED_API_KEY",
        name: "WaveSpeed API Key",
        nodes: ["WaveSpeed Custom Client"],
    },
];

// Lookup: node comfyClass -> setting ID
const NODE_TO_SETTING = {};
for (const entry of API_KEY_SETTINGS) {
    for (const node of entry.nodes) {
        NODE_TO_SETTING[node] = entry.id;
    }
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

const BANNER_ID = "erpk-user-banner";

function createUserBanner(displayName) {
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
    return banner;
}

function tryInjectBanner(displayName) {
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

    container.prepend(createUserBanner(displayName));
}

// Mask API-key values in the settings dialog. ComfyUI's "text" setting type
// renders a plain input showing the full value — not great for secrets. This
// post-render pass switches our four API-key inputs to type="password" (chars
// render as dots) and appends a small monospace preview showing the first four
// and last four characters of the stored value so the user can tell which key
// is configured without the full secret on screen.
function maskApiKey(val) {
    if (!val) return "";
    if (val.length <= 8) return "•".repeat(val.length);
    return `${val.slice(0, 4)}…${val.slice(-4)}`;
}

const API_KEY_LABELS = new Set([
    "Anthropic API Key",
    "Google API Key",
    "OpenAI API Key",
    "WaveSpeed API Key",
]);

function enhanceApiKeyInput(input) {
    if (input.dataset.erpkMasked === "1") return;
    input.dataset.erpkMasked = "1";
    input.type = "password";
    input.autocomplete = "off";
    input.spellcheck = false;

    // Replace the input's default display with a compact "sk-AB…xyz" preview
    // that sits where the input used to be. Clicking the preview swaps in the
    // real password input so the user can edit; blurring the input swaps back
    // to the preview. Matches the AWS Console / GitHub Secrets pattern.
    const preview = document.createElement("div");
    preview.className = "erpk-key-preview";
    preview.setAttribute("role", "button");
    preview.setAttribute("tabindex", "0");
    preview.setAttribute("aria-label", "API key — click to edit");
    preview.style.cssText =
        "display:flex;align-items:center;justify-content:space-between;gap:8px;" +
        "padding:6px 12px;border:1px solid var(--border-color,#3a3a3a);" +
        "border-radius:6px;background:var(--comfy-input-bg,transparent);" +
        "font-family:var(--font-family-monospace,ui-monospace,Menlo,monospace);" +
        "font-size:12px;color:var(--input-text,#ddd);cursor:text;" +
        "min-height:32px;box-sizing:border-box;user-select:none;";

    const valueSpan = document.createElement("span");
    valueSpan.style.cssText =
        "flex:1 1 auto;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" +
        "letter-spacing:0.02em;";

    const editHint = document.createElement("span");
    editHint.textContent = "Edit";
    editHint.style.cssText =
        "opacity:0.5;font-size:10px;flex:0 0 auto;" +
        "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;" +
        "text-transform:uppercase;letter-spacing:0.08em;";

    preview.appendChild(valueSpan);
    preview.appendChild(editHint);

    const updatePreview = () => {
        const val = input.value;
        if (!val) {
            valueSpan.textContent = "Not set";
            valueSpan.style.opacity = "0.5";
        } else {
            valueSpan.textContent = maskApiKey(val);
            valueSpan.style.opacity = "1";
        }
    };

    const showEditing = () => {
        preview.style.display = "none";
        input.style.display = "";
        // setTimeout lets display:"" settle before focus to avoid focus loss
        setTimeout(() => input.focus(), 0);
    };
    const showMasked = () => {
        input.style.display = "none";
        preview.style.display = "flex";
        updatePreview();
    };

    preview.addEventListener("click", showEditing);
    preview.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            showEditing();
        }
    });
    input.addEventListener("blur", showMasked);
    input.addEventListener("input", updatePreview);
    input.addEventListener("keydown", (e) => {
        if (e.key === "Escape") input.blur();
    });

    // Insert preview where the input lives so the layout slot is identical.
    if (input.parentElement) {
        input.parentElement.insertBefore(preview, input);
    }
    updatePreview();
    showMasked();
}

function enhanceApiKeyInputs() {
    const labels = document.querySelectorAll(
        ".p-dialog-content span, .p-dialog-content label, " +
            ".comfy-modal-content span, .comfy-modal-content label"
    );
    for (const el of labels) {
        const text = el.textContent?.trim();
        if (!API_KEY_LABELS.has(text)) continue;
        // Walk up to the row container, then find the text input inside it.
        let container = el;
        let input = null;
        for (let i = 0; i < 6 && container; i++) {
            input = container.querySelector?.(
                "input[type='text'], input[type='password'], input:not([type])"
            );
            if (input) break;
            container = container.parentElement;
        }
        if (input) enhanceApiKeyInput(input);
    }
}

function observeSettingsDialog(displayName) {
    // Watch for dialog open/close to inject the banner and mask API-key inputs.
    const observer = new MutationObserver(() => {
        const dialogOpen =
            document.querySelector(".p-dialog-content") ||
            document.querySelector(".comfy-modal-content");
        if (dialogOpen) {
            tryInjectBanner(displayName);
            enhanceApiKeyInputs();
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });
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
];

function buildSettings() {
    const apiKeySettings = API_KEY_SETTINGS.map((entry) => ({
        id: entry.id,
        name: entry.name,
        type: "text",
        defaultValue: "",
        category: ["ERPK", "API Keys", entry.name],
        tooltip: `${entry.name}. Leave empty to use environment variable or config.ini.`,
    }));
    return [...apiKeySettings, ...GENERAL_SETTINGS];
}

app.registerExtension({
    name: "ERPK.Settings",

    settings: buildSettings(),

    async setup() {
        // Register user context for multi-user settings resolution
        await registerUserContext();

        // Re-register on WebSocket reconnect (client_id may change)
        api.addEventListener("reconnected", () => {
            registerUserContext();
        });

        // Inject user banner into ERPK Settings panel when dialog opens
        const userInfo = await fetchUserInfo();
        if (userInfo.display_name) {
            observeSettingsDialog(userInfo.display_name);
        }
    },

    nodeCreated(node) {
        const settingId = NODE_TO_SETTING[node.comfyClass];
        if (!settingId) return;

        const apiKeyWidget = node.widgets?.find((w) => w.name === "api_key");
        if (!apiKeyWidget) return;

        const settingValue = app.extensionManager.setting.get(settingId);
        if (settingValue && settingValue.trim()) {
            apiKeyWidget.value = "";
            if (apiKeyWidget.inputEl) {
                apiKeyWidget.inputEl.disabled = true;
                apiKeyWidget.inputEl.placeholder = "Configured in Settings";
            }
        }
    },
});
