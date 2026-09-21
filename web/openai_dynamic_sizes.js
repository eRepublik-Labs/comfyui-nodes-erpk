// ABOUTME: Filters the `size` Combo on the OpenAI image nodes to what the selected
// ABOUTME: model accepts, and migrates workflows saved before custom_width/height existed.

import { app } from "../../../scripts/app.js";

const ALL_PRESETS = [
    "auto", "1024x1024", "1024x1536", "1536x1024",
    "2048x2048", "2048x1152", "1152x2048", "3840x2160", "2160x3840",
    "Custom",
];
const SERIES_1024 = ["auto", "1024x1024", "1024x1536", "1536x1024", "Custom"];

// Valid sizes per model for OpenAIImageGeneration. "Custom" is always offered
// because the arbitrary-size envelope and the DALL-E sizes both go through it.
// The client-side _validate_size_for_gpt_image_2 in openai_api/client.py is
// the authoritative safety net for gpt-image-2 and 2.5.
const GEN_SIZE_MAP = {
    "gpt-image-2.5-sunburst": ALL_PRESETS,
    "gpt-image-2.5-flare": ALL_PRESETS,
    "gpt-image-2": ALL_PRESETS,
    "gpt-image-1.5": ["auto", "1024x1024", "1024x1536", "1536x1024", "2048x2048", "Custom"],
    "gpt-image-1": SERIES_1024,
    "gpt-image-1-mini": SERIES_1024,
    "dall-e-3": ["1024x1024", "Custom"],
    "dall-e-2": ["1024x1024", "Custom"],
};

// Valid sizes per model for OpenAIImageEdit (measured live 2026-09-21: the 1.x
// models take only the 1024-series and auto; gpt-image-2 and 2.5 take any size
// in the gpt-image-2 envelope).
const EDIT_SIZE_MAP = {
    "gpt-image-2.5-sunburst": ALL_PRESETS,
    "gpt-image-2.5-flare": ALL_PRESETS,
    "gpt-image-2": ALL_PRESETS,
    "gpt-image-1.5": SERIES_1024,
    "gpt-image-1": SERIES_1024,
    "gpt-image-1-mini": SERIES_1024,
};

// Fallback when the selected model isn't in the map (e.g. a new model ID we
// haven't tracked yet). Permissive superset so users aren't stuck.
const FALLBACK = ALL_PRESETS;

// A workflow saved while size was a free-text widget holds one fewer pair of
// values (no custom_width / custom_height) and may hold a typed size that is
// not a preset. LiteGraph has already assigned those values positionally by
// the time onConfigure runs, so rewrite the widgets themselves: restore the
// size as Custom with the dimensions parsed out and shift the rest back.
export function migrateSizeValues(node, info) {
    const values = info?.widgets_values;
    if (!Array.isArray(values) || !node.widgets) return;
    const sizeIndex = node.widgets.findIndex((w) => w.name === "size");
    if (sizeIndex < 0) return;
    if (values.length !== node.widgets.length - 2) return;

    const saved = values[sizeIndex];
    const match = typeof saved === "string" && saved.match(/^(\d+)x(\d+)$/);
    const isPreset = ALL_PRESETS.includes(saved);
    const size = isPreset ? saved : match ? "Custom" : "1024x1024";
    const width = match && !isPreset ? Number(match[1]) : 1024;
    const height = match && !isPreset ? Number(match[2]) : 1024;

    const migrated = [
        ...values.slice(0, sizeIndex),
        size, width, height,
        ...values.slice(sizeIndex + 1),
    ];
    migrated.forEach((value, i) => {
        if (node.widgets[i]) node.widgets[i].value = value;
    });
}

function installDynamicSizeFilter(nodeType, sizeMap) {
    const origOnConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function (info) {
        const r = origOnConfigure?.apply(this, arguments);
        migrateSizeValues(this, info);
        return r;
    };

    const origOnNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
        const r = origOnNodeCreated?.apply(this, arguments);

        const modelWidget = this.widgets?.find((w) => w.name === "model");
        const sizeWidget = this.widgets?.find((w) => w.name === "size");
        if (!modelWidget || !sizeWidget || sizeWidget.type !== "combo") return r;

        const updateSizeOptions = () => {
            const allowed = sizeMap[modelWidget.value] || FALLBACK;
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
            installDynamicSizeFilter(nodeType, GEN_SIZE_MAP);
        } else if (nodeData.name === "OpenAIImageEdit") {
            installDynamicSizeFilter(nodeType, EDIT_SIZE_MAP);
        }
    },
});
