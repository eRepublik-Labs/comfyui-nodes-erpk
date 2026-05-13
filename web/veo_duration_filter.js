// ABOUTME: Filters the duration_seconds Combo on Veo nodes to the values each model supports.
// ABOUTME: Reflects the per-model duration matrix in https://ai.google.dev/gemini-api/docs/video.

import { app } from "../../../scripts/app.js";

const VEO_DURATIONS_BY_MODEL = {
    "veo-3.1-generate-preview":      ["4", "6", "8"],
    "veo-3.1-fast-generate-preview": ["4", "6", "8"],
    "veo-3.1-lite-generate-preview": ["4", "6", "8"],
    "veo-3.0-generate-001":          ["4", "6", "8"],
    "veo-3.0-fast-generate-001":     ["4", "6", "8"],
    "veo-2.0-generate-001":          ["5", "6", "8"],
};
const FALLBACK_DURATIONS = ["4", "6", "8"];
const VEO_NODES = new Set(["VeoTextToVideo", "VeoImageToVideo"]);

function findWidget(node, name) {
    return node.widgets?.find((w) => w.name === name);
}

function applyDurationFilter(node) {
    const modelWidget = findWidget(node, "model");
    const durWidget = findWidget(node, "duration_seconds");
    if (!modelWidget || !durWidget) return;

    const allowed = VEO_DURATIONS_BY_MODEL[modelWidget.value] ?? FALLBACK_DURATIONS;

    if (durWidget.options) {
        durWidget.options.values = [...allowed];
    }

    // Saved workflows may have numeric values from earlier int-options schema; normalize to string.
    if (typeof durWidget.value === "number") {
        durWidget.value = String(durWidget.value);
    }

    if (!allowed.includes(durWidget.value)) {
        const fallback = allowed.includes("8") ? "8" : allowed[allowed.length - 1];
        console.log(`[ERPK] Veo duration ${durWidget.value}s not allowed on ${modelWidget.value}; resetting to ${fallback}s`);
        durWidget.value = fallback;
    }
}

app.registerExtension({
    name: "erpk.veo_duration_filter",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (!VEO_NODES.has(nodeData.name)) return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = onNodeCreated?.apply(this, arguments);
            setTimeout(() => applyDurationFilter(this), 0);

            const modelWidget = findWidget(this, "model");
            if (modelWidget) {
                const userCallback = modelWidget.callback;
                modelWidget.callback = (value, ...rest) => {
                    const cbResult = userCallback?.call(modelWidget, value, ...rest);
                    applyDurationFilter(this);
                    return cbResult;
                };
            }
            return result;
        };

        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            const result = onConfigure?.apply(this, arguments);
            setTimeout(() => applyDurationFilter(this), 0);
            return result;
        };
    },
});
