// ABOUTME: Captures erpk_inline_preview ui payloads and paints them via node.imgs;
// ABOUTME: an eye-icon toggles visibility by hiding LiteGraph's $$canvas-image-preview widget.
//
// Renderer compatibility: LEGACY LiteGraph canvas renderer only.
// The icon and preview do not render under ComfyUI's Nodes 2.0 (Vue) renderer because
// onDrawForeground / node.imgs are canvas-era hooks with no documented Vue equivalent
// at the time of writing (2026-05-14). Toggle Nodes 2.0 off in Settings to use this feature.

import { app } from "../../../scripts/app.js";

const PAYLOAD_KEY = "erpk_inline_preview";
const PROP_KEY = "erpkInlinePreview";
const PREVIEW_WIDGET_NAME = "$$canvas-image-preview";
const ICON_SIZE = 14;
const ICON_RIGHT_MARGIN = 6;
const BOTTOM_PADDING = 12;

function shouldHook(nodeData) {
    const category = nodeData?.category || "";
    const outputs = nodeData?.output || [];
    return category.startsWith("ERPK/") && outputs.includes("IMAGE");
}

function buildImageUrl(ref) {
    const params = new URLSearchParams({
        filename: ref.filename,
        type: ref.dir_type || "temp",
        subfolder: ref.subfolder || "",
        rand: String(Date.now()),
    });
    return `/api/view?${params.toString()}`;
}

function ensureState(node) {
    if (!node.properties) node.properties = {};
    if (!node.properties[PROP_KEY]) {
        node.properties[PROP_KEY] = { visible: true, ref: null };
    }
    return node.properties[PROP_KEY];
}

function findPreviewWidget(node) {
    return node.widgets?.find((w) => w.name === PREVIEW_WIDGET_NAME);
}

function setPreviewHidden(widget, hidden) {
    if (hidden) {
        if (widget._erpkOrigType === undefined) {
            widget._erpkOrigType = widget.type;
            widget._erpkOrigComputeSize = widget.computeSize;
        }
        widget.type = "hidden";
        widget.computeSize = () => [0, -4];
    } else {
        if (widget._erpkOrigType !== undefined) {
            widget.type = widget._erpkOrigType;
            widget.computeSize = widget._erpkOrigComputeSize;
            delete widget._erpkOrigType;
            delete widget._erpkOrigComputeSize;
        }
    }
}

function paintFromRef(node, ref) {
    const img = new Image();
    img.onload = () => {
        node._erpkCachedImg = img;
        const state = ensureState(node);
        if (state.visible) {
            node.imgs = [img];
            // Widget is created lazily by LiteGraph on a future draw — poll until it exists.
            awaitPreviewWidget(node, () => syncWidgetVisibility(node));
        } else {
            // Preview is off — cache the image for later toggle-on but leave
            // node.imgs empty so LiteGraph paints neither the image nor the
            // "W × H" dimension overlay it derives from node.imgs[0].
            node.imgs = [];
            node.setDirtyCanvas?.(true, true);
        }
    };
    img.onerror = () => {
        console.warn(`[ERPK inline_preview] failed to load ${ref.filename}`);
        node.imgs = [];
        node.setDirtyCanvas(true, true);
    };
    img.src = buildImageUrl(ref);
}

function awaitPreviewWidget(node, callback, attempts = 30) {
    if (findPreviewWidget(node)) {
        callback();
        return;
    }
    if (attempts <= 0) {
        node.setDirtyCanvas?.(true, true);
        return;
    }
    node.setDirtyCanvas?.(true, true);
    requestAnimationFrame(() => awaitPreviewWidget(node, callback, attempts - 1));
}

function syncWidgetVisibility(node) {
    const state = ensureState(node);
    const widget = findPreviewWidget(node);
    if (widget) setPreviewHidden(widget, !state.visible);

    if (node.computeSize) {
        const natural = node.computeSize();
        node.size = [node.size[0], natural[1] + BOTTOM_PADDING];
    }
    node.setDirtyCanvas?.(true, true);
    node.graph?.setDirtyCanvas?.(true, true);
}

function iconRect(node) {
    const titleHeight = window.LiteGraph?.NODE_TITLE_HEIGHT ?? 30;
    return {
        x: node.size[0] - ICON_SIZE - ICON_RIGHT_MARGIN,
        y: -(titleHeight + ICON_SIZE) / 2,
        w: ICON_SIZE,
        h: ICON_SIZE,
    };
}

function hitTest(rect, pos) {
    return pos[0] >= rect.x && pos[0] <= rect.x + rect.w
        && pos[1] >= rect.y && pos[1] <= rect.y + rect.h;
}

function drawEyeIcon(ctx, x, y, size, active) {
    ctx.save();
    ctx.translate(x, y);
    const s = size / 16;
    ctx.scale(s, s);

    const color = active ? "#5a9dff" : "#888";
    ctx.lineWidth = 1.6;
    ctx.strokeStyle = color;
    ctx.fillStyle = active ? color : "transparent";

    ctx.beginPath();
    ctx.moveTo(1, 8);
    ctx.bezierCurveTo(4, 3, 12, 3, 15, 8);
    ctx.bezierCurveTo(12, 13, 4, 13, 1, 8);
    ctx.closePath();
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(8, 8, 2.8, 0, Math.PI * 2);
    if (active) ctx.fill();
    else ctx.stroke();

    if (!active) {
        ctx.beginPath();
        ctx.moveTo(2, 2);
        ctx.lineTo(14, 14);
        ctx.lineWidth = 1.8;
        ctx.strokeStyle = "#888";
        ctx.stroke();
    }

    ctx.restore();
}

app.registerExtension({
    name: "erpk.inline_preview",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (!shouldHook(nodeData)) return;

        const onDrawForeground = nodeType.prototype.onDrawForeground;
        nodeType.prototype.onDrawForeground = function (ctx) {
            onDrawForeground?.apply(this, arguments);
            if (this.flags?.collapsed) return;
            const state = this.properties?.[PROP_KEY];
            const rect = iconRect(this);
            drawEyeIcon(ctx, rect.x, rect.y, rect.w, !!state?.visible);
        };

        const onMouseDown = nodeType.prototype.onMouseDown;
        nodeType.prototype.onMouseDown = function (event, pos, graphCanvas) {
            if (hitTest(iconRect(this), pos)) {
                const state = ensureState(this);
                state.visible = !state.visible;
                if (state.visible) {
                    // Toggling on: restore the cached image, or repaint from
                    // ref if the image wasn't cached (e.g. after a reload that
                    // started with visible=false).
                    if (this._erpkCachedImg) {
                        this.imgs = [this._erpkCachedImg];
                        awaitPreviewWidget(this, () => syncWidgetVisibility(this));
                    } else if (state.ref) {
                        paintFromRef(this, state.ref);
                    } else {
                        syncWidgetVisibility(this);
                    }
                } else {
                    // Toggling off: clear node.imgs so LiteGraph stops drawing
                    // both the image and its "W × H" dimension overlay (the
                    // overlay reads node.imgs[0] directly and is not gated by
                    // the widget's hidden state).
                    this.imgs = [];
                    syncWidgetVisibility(this);
                }
                this.setDirtyCanvas?.(true, true);
                return true;
            }
            return onMouseDown?.apply(this, arguments);
        };

        const onMouseMove = nodeType.prototype.onMouseMove;
        nodeType.prototype.onMouseMove = function (event, pos, graphCanvas) {
            const canvas = graphCanvas?.canvas;
            if (canvas) {
                const overIcon = hitTest(iconRect(this), pos);
                canvas.style.cursor = overIcon ? "pointer" : "";
            }
            return onMouseMove?.apply(this, arguments);
        };

        const onMouseLeave = nodeType.prototype.onMouseLeave;
        nodeType.prototype.onMouseLeave = function (event, pos, graphCanvas) {
            const canvas = graphCanvas?.canvas;
            if (canvas) canvas.style.cursor = "";
            return onMouseLeave?.apply(this, arguments);
        };

        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            onExecuted?.apply(this, arguments);
            const entries = message?.[PAYLOAD_KEY];
            if (!Array.isArray(entries) || entries.length === 0) return;
            const imageEntry = entries.find((e) => e?.type === "image");
            if (!imageEntry) return;

            const state = ensureState(this);
            state.ref = {
                filename: imageEntry.filename,
                subfolder: imageEntry.subfolder || "",
                dir_type: imageEntry.dir_type || "temp",
                width: imageEntry.width,
                height: imageEntry.height,
            };
            paintFromRef(this, state.ref);
        };

        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            const r = onConfigure?.apply(this, arguments);
            const saved = info?.properties?.[PROP_KEY];
            if (saved && typeof saved === "object") {
                ensureState(this);
                Object.assign(this.properties[PROP_KEY], saved);
            }
            const state = this.properties?.[PROP_KEY];
            if (state?.ref && state?.visible) {
                setTimeout(() => paintFromRef(this, state.ref), 30);
            }
            return r;
        };
    },
});
