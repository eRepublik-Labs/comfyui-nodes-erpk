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

function observeSettingsDialog(displayName) {
    // Watch for dialog open/close to inject the banner
    const observer = new MutationObserver(() => {
        const dialogOpen =
            document.querySelector(".p-dialog-content") ||
            document.querySelector(".comfy-modal-content");
        if (dialogOpen) {
            tryInjectBanner(displayName);
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
