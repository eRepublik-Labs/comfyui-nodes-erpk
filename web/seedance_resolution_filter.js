// ABOUTME: Hides 480p from the resolution Combo on Seedance 2.0 nodes when the Turbo tier is selected.
// ABOUTME: Turbo endpoint only accepts 720p and 1080p; standard and Fast accept all three.

import { app } from "../../../scripts/app.js";

const TURBO_RESOLUTIONS = ["720p", "1080p"];
const FULL_RESOLUTIONS = ["480p", "720p", "1080p"];
const SEEDANCE_NODES = new Set([
    "Seedance20TextToVideoNode",
    "Seedance20ImageToVideoNode",
]);

function findWidget(node, name) {
    return node.widgets?.find((w) => w.name === name);
}

function applyResolutionFilter(node) {
    const modelWidget = findWidget(node, "model");
    const resWidget = findWidget(node, "resolution");
    if (!modelWidget || !resWidget) return;

    const isTurbo = typeof modelWidget.value === "string" && modelWidget.value.includes("Turbo");
    const allowed = isTurbo ? TURBO_RESOLUTIONS : FULL_RESOLUTIONS;

    if (resWidget.options) {
        resWidget.options.values = [...allowed];
    }

    if (!allowed.includes(resWidget.value)) {
        const fallback = allowed[0];
        console.log(`[ERPK] Seedance resolution ${resWidget.value} not allowed on ${modelWidget.value}; resetting to ${fallback}`);
        resWidget.value = fallback;
    }
}

app.registerExtension({
    name: "erpk.seedance_resolution_filter",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (!SEEDANCE_NODES.has(nodeData.name)) return;

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
