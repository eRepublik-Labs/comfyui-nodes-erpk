// ABOUTME: ComfyUI extension to show aspect ratio in node title and sync preset dimensions
// ABOUTME: Updates node title dynamically and syncs width/height when preset changes

import { app } from "../../scripts/app.js";

const SEEDREAM_NODES = new Set([
    "WaveSpeed Custom SeedreamV4",
    "WaveSpeed Custom SeedreamV4Edit",
    "WaveSpeed Custom SeedreamV4Sequential",
    "WaveSpeed Custom SeedreamV4EditSequential",
    "WaveSpeed Custom SeedreamV4_5",
    "WaveSpeed Custom SeedreamV4_5Edit",
    "WaveSpeed Custom SeedreamV4_5Sequential",
    "WaveSpeed Custom SeedreamV4_5EditSequential",
]);

const originalTitles = new WeakMap();
const setupNodes = new WeakSet();
const hookedWidgets = new WeakSet();

function gcd(a, b) {
    a = Math.abs(Math.round(a));
    b = Math.abs(Math.round(b));
    while (b > 0) {
        const temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

function calculateAspectRatio(width, height) {
    if (!width || !height || width <= 0 || height <= 0) return null;
    const divisor = gcd(width, height);
    let w = width / divisor;
    let h = height / divisor;
    while (w > 50 || h > 50) {
        if (w % 2 === 0 && h % 2 === 0) {
            w /= 2;
            h /= 2;
        } else break;
    }
    return `${Math.round(w)}:${Math.round(h)}`;
}

function parseDimensionsFromPreset(presetValue) {
    if (!presetValue || presetValue === "Custom") return null;
    const match = presetValue.match(/\((\d+)x(\d+)\)/);
    if (match) {
        return { width: parseInt(match[1], 10), height: parseInt(match[2], 10) };
    }
    return null;
}

function updateNodeTitle(node) {
    if (!node?.widgets) return;

    const showRatioWidget = node.widgets.find(w => w.name === "show_aspect_ratio");
    const showRatio = showRatioWidget ? showRatioWidget.value : true;

    const widthWidget = node.widgets.find(w => w.name === "width");
    const heightWidget = node.widgets.find(w => w.name === "height");

    if (!widthWidget || !heightWidget) return;

    if (!originalTitles.has(node)) {
        originalTitles.set(node, node.title);
    }

    const originalTitle = originalTitles.get(node);

    if (showRatio) {
        const ratio = calculateAspectRatio(widthWidget.value, heightWidget.value);
        node.title = ratio ? `${originalTitle} [${ratio}]` : originalTitle;
    } else {
        node.title = originalTitle;
    }

    node.setDirtyCanvas?.(true, true);
}

function updateDimensionsFromPreset(node, presetValue, widthWidget, heightWidget) {
    const dims = parseDimensionsFromPreset(presetValue);
    if (dims) {
        widthWidget.value = dims.width;
        heightWidget.value = dims.height;
    }
}

function hookWidget(widget, node, onChange) {
    if (hookedWidgets.has(widget)) return;

    let currentValue = widget.value;
    Object.defineProperty(widget, 'value', {
        get() { return currentValue; },
        set(v) {
            const oldValue = currentValue;
            currentValue = v;
            if (onChange) onChange(v, oldValue);
            updateNodeTitle(node);
        },
        configurable: true,
        enumerable: true
    });
    hookedWidgets.add(widget);
}

function setupNode(node) {
    if (!node?.widgets) return;
    if (setupNodes.has(node)) return;
    setupNodes.add(node);

    const widthWidget = node.widgets.find(w => w.name === "width");
    const heightWidget = node.widgets.find(w => w.name === "height");
    const presetWidget = node.widgets.find(w => w.name === "size_preset");
    const showRatioWidget = node.widgets.find(w => w.name === "show_aspect_ratio");

    if (!widthWidget || !heightWidget) return;

    if (!originalTitles.has(node)) {
        originalTitles.set(node, node.title);
    }

    hookWidget(widthWidget, node);
    hookWidget(heightWidget, node);

    if (presetWidget) {
        hookWidget(presetWidget, node, (newValue) => {
            updateDimensionsFromPreset(node, newValue, widthWidget, heightWidget);
        });
    }

    if (showRatioWidget) {
        hookWidget(showRatioWidget, node);
    }

    updateNodeTitle(node);
}

app.registerExtension({
    name: "WaveSpeed.AspectRatioTitle",

    beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (!SEEDREAM_NODES.has(nodeData.name)) return;

        const origOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function() {
            const r = origOnNodeCreated?.apply(this, arguments);
            setTimeout(() => setupNode(this), 200);
            return r;
        };
    },

    loadedGraphNode(node, app) {
        if (!SEEDREAM_NODES.has(node.type)) return;
        setTimeout(() => setupNode(node), 200);
    }
});
