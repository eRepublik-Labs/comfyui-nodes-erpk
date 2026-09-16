// ABOUTME: Maps saved MiniMax H3 video resolutions from the open-weights tiers to the official 768p/2k tiers.
// ABOUTME: Runs on workflow load so a 480p/540p/1080p value saved before the edition switch still validates.

import { app } from "../../../scripts/app.js";

const H3_VIDEO_NODES = new Set([
    "MinimaxH3TextToVideoNode",
    "MinimaxH3ImageToVideoNode",
    "MinimaxH3ReferenceToVideoNode",
]);

// Open-weights tiers that no longer exist on the MiniMax-hosted endpoint.
const RESOLUTION_MAP = { "480p": "768p", "540p": "768p", "1080p": "2k" };
// 9:21 exists only on the open-weights edition.
const ASPECT_MAP = { "9:21": "9:16" };

function migrate(node) {
    for (const widget of node.widgets ?? []) {
        if (widget.name === "resolution" && RESOLUTION_MAP[widget.value]) {
            console.log(`[ERPK] MiniMax H3 resolution ${widget.value} is not offered by the MiniMax-hosted endpoint; using ${RESOLUTION_MAP[widget.value]}`);
            widget.value = RESOLUTION_MAP[widget.value];
        }
        if (widget.name === "aspect_ratio" && ASPECT_MAP[widget.value]) {
            console.log(`[ERPK] MiniMax H3 aspect ratio ${widget.value} is not offered by the MiniMax-hosted endpoint; using ${ASPECT_MAP[widget.value]}`);
            widget.value = ASPECT_MAP[widget.value];
        }
        if (widget.name === "duration" && typeof widget.value === "number" && widget.value < 4) {
            widget.value = 4;
        }
    }
}

app.registerExtension({
    name: "erpk.minimax_h3_resolution_migration",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (!H3_VIDEO_NODES.has(nodeData.name)) return;

        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            const result = onConfigure?.apply(this, arguments);
            migrate(this);
            return result;
        };
    },
});
