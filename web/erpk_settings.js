// ABOUTME: Registers ERPK API key settings in ComfyUI Settings UI and canvas context menu
// ABOUTME: Makes node api_key widgets read-only when keys are configured in Settings

import { app } from "../../scripts/app.js";

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

app.registerExtension({
    name: "ERPK.Settings",

    settings: API_KEY_SETTINGS.map((entry) => ({
        id: entry.id,
        name: entry.name,
        type: "text",
        defaultValue: "",
        category: ["ERPK", "API Keys", entry.name],
        tooltip: `${entry.name}. Leave empty to use environment variable or config.ini.`,
    })),

    setup() {
        const origGetCanvasMenuOptions =
            LGraphCanvas.prototype.getCanvasMenuOptions;
        LGraphCanvas.prototype.getCanvasMenuOptions = function (...args) {
            const options = origGetCanvasMenuOptions.apply(this, [...args]);
            options.push(null);
            options.push({
                content: "ERPK Settings",
                callback: () => {
                    const btn = document.querySelector(".comfy-settings-btn");
                    if (!btn) return;
                    btn.click();
                    // Poll for the search box in the settings dialog and type "ERPK"
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
