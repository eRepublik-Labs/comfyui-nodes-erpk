// ABOUTME: Pure helpers that read or size the litegraph node behind the region editor.
// ABOUTME: Every function takes the node explicitly; no app, DOM, or shared editor state.
// @ts-check

import {
    MIN_NODE_WIDTH,
    CHROME_HORIZONTAL_INSET,
    ROOT_PADDING_H,
    CANVAS_MIN_H,
    EDITOR_CHROME_V,
    REMOVAL_FILL_OPTIONS,
    DEFAULT_REMOVAL_FILL,
    DEFAULT_CHROMA_COLOR,
    HEX_COLOR_RE,
} from "./constants.js";

export function findWidget(node, name) {
    return node.widgets?.find((w) => w.name === name) ?? null;
}

// LiteGraph restores widget values by position (widgets_values[i]), and the
// canvas DOM widget serializes a trailing entry after the Python widgets. A
// workflow saved when removal_fill and chroma_color did not exist therefore
// lands that trailing entry in removal_fill's slot, and ComfyUI refuses to
// queue a combo value outside its option list. Hold both widgets to a legal
// value so a restored workflow stays queueable.
export function repairManagedWidgetValues(node) {
    const fill = findWidget(node, "removal_fill");
    if (fill && !REMOVAL_FILL_OPTIONS.includes(fill.value)) {
        fill.value = DEFAULT_REMOVAL_FILL;
    }
    const color = findWidget(node, "chroma_color");
    if (color && !HEX_COLOR_RE.test(color.value)) {
        color.value = DEFAULT_CHROMA_COLOR;
    }
}

export function frameDims(node) {
    const w = Number(findWidget(node, "width")?.value) || 1024;
    const h = Number(findWidget(node, "height")?.value) || 1024;
    return { w: Math.max(w, 1), h: Math.max(h, 1) };
}

export function frameAspect(node) {
    const dims = frameDims(node);
    return dims.w / dims.h;
}

// Height the editor needs below the regular widgets: a canvas matching the
// frame's aspect ratio at the node's current width, clamped to a usable band.
// Wired into the DOM widget's getMinHeight/getMaxHeight so the layout pins
// the editor at exactly this height instead of treating it as growable.
export function desiredEditorHeight(node) {
    const innerW = Math.max(
        (node.size?.[0] ?? MIN_NODE_WIDTH) - CHROME_HORIZONTAL_INSET - ROOT_PADDING_H,
        100,
    );
    const canvasH = Math.max(innerW / frameAspect(node), CANVAS_MIN_H);
    return Math.round(canvasH + EDITOR_CHROME_V);
}

// The DOM widget wrapper's width resolves from a JavaScript-positioned
// container that can lag the node size on load; pin the root to the node
// width explicitly on every "size has changed" path.
export function pinRootWidth(node) {
    const root = node?._erpkRegionEditor?.root;
    // While expanded the root is a viewport overlay, not a node-width box.
    if (!root || root._erpkExpanded) return;
    const w = Math.max((node.size?.[0] ?? MIN_NODE_WIDTH) - CHROME_HORIZONTAL_INSET, 100);
    root.style.width = w + "px";
    root.style.maxWidth = w + "px";
}

// Classic LiteGraph checks widget.hidden; Nodes 2.0 (Vue) checks widget.options.hidden.
// Set both so visibility works in either renderer.
export function setWidgetHidden(widget, hidden) {
    widget.hidden = hidden;
    if (!widget.options) widget.options = {};
    widget.options.hidden = hidden;
}

// LoadImage and executed preview nodes expose their image client-side via
// node.imgs; follow the link on the named input to its origin node.
export function upstreamImage(node, inputName) {
    const input = node.inputs?.find((i) => i.name === inputName);
    if (!input || input.link == null) return null;
    const link = node.graph?.links?.[input.link];
    const origin = link ? node.graph.getNodeById(link.origin_id) : null;
    return origin?.imgs?.[0] ?? null;
}
