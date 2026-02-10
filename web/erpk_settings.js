// ABOUTME: Registers ERPK API key settings in ComfyUI Settings UI
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
        "display:flex;align-items:center;gap:8px;padding:8px 12px;" +
        "background:#1a2744;color:#5b8def;border:1px solid #2a3f6b;" +
        "border-radius:6px;font-size:13px;margin-bottom:8px;";

    const icon = document.createElement("span");
    icon.style.fontSize = "16px";
    icon.textContent = "\u{1F464}";

    const text = document.createElement("span");
    text.textContent = "Current user: " + displayName;

    banner.appendChild(icon);
    banner.appendChild(text);
    return banner;
}

function tryInjectBanner(displayName) {
    if (document.getElementById(BANNER_ID)) return;

    // Find ERPK settings by looking for our setting labels in the dialog
    const allText = document.querySelectorAll(
        ".p-dialog-content span, .p-dialog-content label, " +
            ".comfy-modal-content span, .comfy-modal-content label"
    );
    for (const el of allText) {
        if (el.textContent.trim() === "Anthropic API Key") {
            // Walk up to the scrollable settings container
            const container =
                el.closest(".p-dialog-content") ||
                el.closest(".comfy-modal-content") ||
                el.closest("[class*='settings']");
            if (container) {
                container.prepend(createUserBanner(displayName));
            }
            return;
        }
    }
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

function buildSettings() {
    return API_KEY_SETTINGS.map((entry) => ({
        id: entry.id,
        name: entry.name,
        type: "text",
        defaultValue: "",
        category: ["ERPK", "API Keys", entry.name],
        tooltip: `${entry.name}. Leave empty to use environment variable or config.ini.`,
    }));
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
