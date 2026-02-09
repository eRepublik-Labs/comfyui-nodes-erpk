// ABOUTME: Registers ERPK API key settings in ComfyUI Settings UI and canvas context menu
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

        // Fetch user info and show indicator in multi-user mode
        const userInfo = await fetchUserInfo();
        if (userInfo.multi_user) {
            const indicator = document.createElement("div");
            indicator.className = "erpk-user-indicator";
            indicator.textContent = `Settings for: ${userInfo.display_name}`;
            indicator.style.cssText =
                "position:fixed;bottom:4px;right:4px;padding:4px 8px;" +
                "background:rgba(0,0,0,0.6);color:#ccc;font-size:11px;" +
                "border-radius:4px;z-index:9999;pointer-events:none;";
            document.body.appendChild(indicator);
        }

        // Add ERPK Settings to canvas context menu
        const origGetCanvasMenuOptions =
            LGraphCanvas.prototype.getCanvasMenuOptions;
        LGraphCanvas.prototype.getCanvasMenuOptions = function (...args) {
            const options = origGetCanvasMenuOptions.apply(this, [...args]);
            options.push(null);
            options.push({
                content: "⚙️ ERPK Settings",
                callback: () => {
                    const btn = document.querySelector(".comfy-settings-btn");
                    if (!btn) return;
                    btn.click();
                    let attempts = 0;
                    const searchERPK = () => {
                        const input = document.querySelector(
                            ".settings-search-box input"
                        );
                        if (input) {
                            const setter = Object.getOwnPropertyDescriptor(
                                HTMLInputElement.prototype,
                                "value"
                            ).set;
                            setter.call(input, "ERPK");
                            input.dispatchEvent(
                                new Event("input", { bubbles: true })
                            );
                            return;
                        }
                        if (++attempts < 10) {
                            setTimeout(searchERPK, 100);
                        }
                    };
                    setTimeout(searchERPK, 100);
                },
            });
            return options;
        };
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
