// ABOUTME: Filters the resolution Combo on Veo nodes to the values each model supports.
// ABOUTME: Reflects the per-model capability matrix in https://ai.google.dev/gemini-api/docs/video.

import { app } from "../../../scripts/app.js";

const VEO_RESOLUTIONS_BY_MODEL = {
    "veo-3.1-generate-preview":      ["720p", "1080p", "4k"],
    "veo-3.1-fast-generate-preview": ["720p", "1080p", "4k"],
    "veo-3.1-lite-generate-preview": ["720p", "1080p"],
    "veo-3.0-generate-001":          ["720p", "1080p"],
    "veo-3.0-fast-generate-001":     ["720p", "1080p"],
    "veo-2.0-generate-001":          ["720p"],
};
const FALLBACK_RESOLUTIONS = ["720p", "1080p", "4k"];
const VEO_NODES = new Set(["VeoTextToVideo", "VeoImageToVideo"]);

function findWidget(node, name) {
    return node.widgets?.find((w) => w.name === name);
}

function applyResolutionFilter(node) {
    const modelWidget = findWidget(node, "model");
    const resWidget = findWidget(node, "resolution");
    if (!modelWidget || !resWidget) return;

    const allowed = VEO_RESOLUTIONS_BY_MODEL[modelWidget.value] ?? FALLBACK_RESOLUTIONS;

    if (resWidget.options) {
        resWidget.options.values = [...allowed];
    }

    if (!allowed.includes(resWidget.value)) {
        const fallback = allowed.includes("1080p") ? "1080p" : allowed[0];
        console.log(`[ERPK] Veo resolution ${resWidget.value} not allowed on ${modelWidget.value}; resetting to ${fallback}`);
        resWidget.value = fallback;
    }
}

app.registerExtension({
    name: "erpk.veo_resolution_filter",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (!VEO_NODES.has(nodeData.name)) return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = onNodeCreated?.apply(this, arguments);
            setTimeout(() => applyResolutionFilter(this), 0);

            const modelWidget = findWidget(this, "model");
            if (modelWidget) {
                const userCallback = modelWidget.callback;
                modelWidget.callback = (value, ...rest) => {
                    const cbResult = userCallback?.call(modelWidget, value, ...rest);
                    applyResolutionFilter(this);
                    return cbResult;
                };
            }
            return result;
        };

        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            const result = onConfigure?.apply(this, arguments);
            setTimeout(() => applyResolutionFilter(this), 0);
            return result;
        };
    },
});
