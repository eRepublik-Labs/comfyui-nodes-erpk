// ABOUTME: Dynamically filter the `size` Combo on OpenAI image nodes based on the
// ABOUTME: selected model, so users can't pick sizes the model will reject.

import { app } from "../../../scripts/app.js";

// Valid sizes per model for OpenAIImageGeneration.
// Kept narrow to what OpenAI's docs explicitly support; widen if a user reports
// missing options. The client-side _validate_size_for_gpt_image_2 in
// openai_api/client.py is the authoritative safety net for edge cases.
const GEN_SIZE_MAP = {
    "gpt-image-2": [
        "auto",
        "1024x1024", "1024x1536", "1536x1024",
        "2048x2048", "2048x1152", "2560x1440",
        "3840x2160", "2160x3840",
    ],
    "gpt-image-1.5": [
        "auto",
        "1024x1024", "1024x1536", "1536x1024",
        "2048x2048",
    ],
    "gpt-image-1": [
        "auto",
        "1024x1024", "1024x1536", "1536x1024",
    ],
    "gpt-image-1-mini": [
        "auto",
        "1024x1024", "1024x1536", "1536x1024",
    ],
    "dall-e-3": [
        "1024x1024", "1792x1024", "1024x1792",
    ],
    "dall-e-2": [
        "256x256", "512x512", "1024x1024",
    ],
};

// Valid sizes per model for OpenAIImageEdit.
// Per OpenAI docs the edit endpoint is tighter than generate — even gpt-image-2
// is limited to the 1024-series and auto.
const EDIT_SIZE_MAP = {
    "gpt-image-2": ["auto", "1024x1024", "1024x1536", "1536x1024"],
    "gpt-image-1.5": ["auto", "1024x1024", "1024x1536", "1536x1024"],
    "gpt-image-1": ["auto", "1024x1024", "1024x1536", "1536x1024"],
    "gpt-image-1-mini": ["auto", "1024x1024", "1024x1536", "1536x1024"],
    "chatgpt-image-latest": ["auto", "1024x1024", "1024x1536", "1536x1024"],
};

// Fallback when the selected model isn't in the map (e.g. a new model ID we
// haven't tracked yet). Permissive superset so users aren't stuck.
const GEN_FALLBACK = [
    "auto",
    "1024x1024", "1024x1536", "1536x1024",
    "512x512", "256x256",
    "1792x1024", "1024x1792",
];
const EDIT_FALLBACK = ["auto", "1024x1024", "1024x1536", "1536x1024"];

function installDynamicSizeFilter(nodeType, sizeMap, fallback) {
    const origOnNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
        const r = origOnNodeCreated?.apply(this, arguments);

        const modelWidget = this.widgets?.find((w) => w.name === "model");
        const sizeWidget = this.widgets?.find((w) => w.name === "size");
        if (!modelWidget || !sizeWidget) return r;

        const updateSizeOptions = () => {
            const allowed = sizeMap[modelWidget.value] || fallback;
            sizeWidget.options.values = allowed;
            // If the current size isn't valid for the new model, snap to a
            // sensible default: prefer "1024x1024" if allowed, else first entry.
            if (!allowed.includes(sizeWidget.value)) {
                sizeWidget.value = allowed.includes("1024x1024")
                    ? "1024x1024"
                    : allowed[0];
            }
            app.graph?.setDirtyCanvas?.(true, true);
        };

        // Initial pass — model widget's default value on node creation.
        updateSizeOptions();

        // Hook the model widget's change callback so size options update live.
        const origCallback = modelWidget.callback;
        modelWidget.callback = function (value) {
            const out = origCallback ? origCallback.call(this, value) : undefined;
            updateSizeOptions();
            return out;
        };

        return r;
    };
}

app.registerExtension({
    name: "erpk.openai.dynamic_sizes",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "OpenAIImageGeneration") {
            installDynamicSizeFilter(nodeType, GEN_SIZE_MAP, GEN_FALLBACK);
        } else if (nodeData.name === "OpenAIImageEdit") {
            installDynamicSizeFilter(nodeType, EDIT_SIZE_MAP, EDIT_FALLBACK);
        }
    },
});
