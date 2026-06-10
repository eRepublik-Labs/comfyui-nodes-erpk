// ABOUTME: Canvas region editor for the RegionalPromptBuilder node — draw, move, resize, and annotate boxes.
// ABOUTME: Serializes normalized regions into the hidden regions_data widget that the Python prompt builder parses.

import { app } from "../../../scripts/app.js";

const NODE_ID = "RegionalPromptBuilder";
const MIN_REGION_SIZE = 0.01;   // normalized floor; Python skips regions at or below 0.005
const HANDLE_HIT_PX = 7;
const HANDLE_DRAW_PX = 6;
const STAGE_PADDING_PX = 0;
const LABEL_FONT = "11px 'Segoe UI', sans-serif";
const MIN_NODE_WIDTH = 340;
// Per-side inset ComfyUI applies between the outer node frame and the inner
// widget area; the DOM widget wrapper is wider than the usable area without it.
const CHROME_HORIZONTAL_INSET = 16;
// Absolute floor for degenerate aspect ratios; otherwise the canvas height
// follows the frame aspect exactly so the canvas always spans the full width.
const CANVAS_MIN_H = 60;
// Matches DESC_INPUT_COUNT on the Python side: desc_1..desc_6 sockets.
const REGION_DESC_INPUTS = 6;

// Grid cell size is expressed in frame pixels, so the grid quantizes to the
// generated image's own pixel space (64 aligns with latent blocks).
const GRID_MIN_CELL_PX = 8;
const GRID_MAX_CELL_PX = 1024;
const GRID_DEFAULT_CELL_PX = 64;
const GRID_DEFAULT_COLOR = "#26262e";
// Destructive-action red for the clear-all control.
const DANGER_RED = "#e5484d";
const DANGER_RED_DIM = "rgba(229, 72, 77, 0.85)";
const DANGER_RED_BORDER = "rgba(229, 72, 77, 0.40)";

// Hover states need real CSS pseudo-classes; !important outweighs the inline
// base styles the elements carry. The danger rule comes last so it wins over
// the generic button rule on the red controls.
const hoverStyles = document.createElement("style");
hoverStyles.textContent = `
.erpk-region-row:hover { background: rgba(255, 255, 255, 0.07); }
.erpk-strip-btn:hover:not(:disabled) {
    color: rgba(255, 255, 255, 0.95) !important;
    border-color: rgba(255, 255, 255, 0.45) !important;
}
.erpk-input:hover:not(:disabled) {
    border-color: rgba(255, 255, 255, 0.30) !important;
}
.erpk-input:focus {
    border-color: rgba(255, 255, 255, 0.50) !important;
    outline: none;
}
.erpk-btn-danger:hover:not(:disabled) {
    color: ${DANGER_RED} !important;
    border-color: ${DANGER_RED} !important;
}
`;
document.head.appendChild(hoverStyles);
// Horizontal padding the editor root carries inside the DOM widget wrapper.
const ROOT_PADDING_H = 12;
const STATUS_STRIP_H = 22;
const INSPECTOR_H = 26;
// Vertical chrome around the canvas inside the editor root: panel padding,
// canvas border, the inspector row, the status strip, and the flex gaps.
const EDITOR_CHROME_V = 70;

// The canvas is a stage for the image-to-be: dark like every ComfyUI content
// preview, independent of the UI theme. Chrome around it follows the theme.
const STAGE_BG = "#101014";
const PANEL_BG = "#16161c";
const PANEL_INPUT_BG = "#0d0d12";
const HAIRLINE = "rgba(255, 255, 255, 0.10)";
const HAIRLINE_STRONG = "rgba(255, 255, 255, 0.25)";
const INK_ON_TAPE = "#0b0b0e";

// Regions cycle through gaffer-tape hues so each keeps a stable identity on
// the stage; kind is marked by the T badge and rendered text, not by color.
const TAPE_COLORS = ["#4cc9f0", "#f9a826", "#f15bb5", "#9ef01a", "#9b5de5", "#ff6d5a"];

function regionColor(index) {
    return TAPE_COLORS[index % TAPE_COLORS.length];
}

// Copy buffer of plain region data; module-level so clones carry between
// editor instances within the page session.
let regionClipboard = [];

function clamp(v, lo, hi) {
    return Math.min(Math.max(v, lo), hi);
}

function round4(v) {
    return Math.round(v * 10000) / 10000;
}

function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function findWidget(node, name) {
    return node.widgets?.find((w) => w.name === name) ?? null;
}

function frameDims(node) {
    const w = Number(findWidget(node, "width")?.value) || 1024;
    const h = Number(findWidget(node, "height")?.value) || 1024;
    return { w: Math.max(w, 1), h: Math.max(h, 1) };
}

function frameAspect(node) {
    const dims = frameDims(node);
    return dims.w / dims.h;
}

// Height the editor needs below the regular widgets: a canvas matching the
// frame's aspect ratio at the node's current width, clamped to a usable band.
// Wired into the DOM widget's getMinHeight/getMaxHeight so the layout pins
// the editor at exactly this height instead of treating it as growable.
function desiredEditorHeight(node) {
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
function pinRootWidth(node) {
    const root = node?._erpkRegionEditor?.root;
    if (!root) return;
    const w = Math.max((node.size?.[0] ?? MIN_NODE_WIDTH) - CHROME_HORIZONTAL_INSET, 100);
    root.style.width = w + "px";
    root.style.maxWidth = w + "px";
}

// Classic LiteGraph checks widget.hidden; Nodes 2.0 (Vue) checks widget.options.hidden.
// Set both so visibility works in either renderer.
function setWidgetHidden(widget, hidden) {
    widget.hidden = hidden;
    if (!widget.options) widget.options = {};
    widget.options.hidden = hidden;
}

// Defensive mirror of the Python-side regions_data contract: invalid JSON or a
// non-list payload yields no regions, malformed entries are skipped, coordinates
// are clamped into the unit square, and near-zero boxes are dropped.
function parseRegions(text) {
    let data;
    try {
        data = JSON.parse(text);
    } catch (_) {
        return [];
    }
    if (!Array.isArray(data)) return [];

    const regions = [];
    for (const entry of data) {
        if (typeof entry !== "object" || entry === null || Array.isArray(entry)) continue;
        const nums = [entry.x, entry.y, entry.w, entry.h].map((v) => Number(v ?? 0));
        if (!nums.every(Number.isFinite)) continue;
        const x = clamp(nums[0], 0, 1);
        const y = clamp(nums[1], 0, 1);
        const w = clamp(nums[2], 0, 1 - x);
        const h = clamp(nums[3], 0, 1 - y);
        if (w <= 0.005 || h <= 0.005) continue;
        regions.push({
            x, y, w, h,
            kind: entry.kind === "text" ? "text" : "object",
            desc: typeof entry.desc === "string" ? entry.desc : "",
            text: typeof entry.text === "string" ? entry.text : "",
        });
    }
    return regions;
}

function serializeRegions(boxes) {
    return JSON.stringify(boxes.map((b) => ({
        x: round4(b.x),
        y: round4(b.y),
        w: round4(b.w),
        h: round4(b.h),
        kind: b.kind,
        desc: b.desc,
        text: b.text,
    })));
}

// Axis-aligned rect from two corner points (both already clamped to the unit
// square), normalizing inverted drags into positive width/height.
function rectFrom(a, b) {
    return {
        x: Math.min(a.x, b.x),
        y: Math.min(a.y, b.y),
        w: Math.abs(a.x - b.x),
        h: Math.abs(a.y - b.y),
    };
}

function enforceMinSize(box) {
    box.w = Math.max(box.w, MIN_REGION_SIZE);
    box.h = Math.max(box.h, MIN_REGION_SIZE);
    box.x = clamp(box.x, 0, 1 - box.w);
    box.y = clamp(box.y, 0, 1 - box.h);
}

// Inspector controls sit in the stage's color world rather than following
// the UI theme, matching the canvas and status strip around them.
function styleInput(el) {
    el.classList.add("erpk-input");
    el.style.background = PANEL_INPUT_BG;
    el.style.color = "rgba(255, 255, 255, 0.9)";
    el.style.border = "1px solid rgba(255, 255, 255, 0.14)";
    el.style.borderRadius = "3px";
    el.style.padding = "4px 6px";
    el.style.fontSize = "12px";
    el.style.boxSizing = "border-box";
    el.style.width = "100%";
}

function createRegionEditor(node) {
    const state = {
        boxes: [],
        selection: new Set(),  // selected region objects — identity survives reorder
        primary: null,         // most recently selected region; inspector binds to it
        drag: null,      // {mode: "create"|"move"|"resize"|"marquee", ...}
        cssW: 0,
        cssH: 0,
        hideBoxes: false,      // view-only: skip drawing and hit-testing boxes
        gridShow: false,
        gridCellPx: GRID_DEFAULT_CELL_PX,
        gridColor: GRID_DEFAULT_COLOR,
        gridAlpha: 1,
        snapOn: false,
    };

    // --- DOM scaffold -------------------------------------------------
    // One continuous panel surface: canvas, inspector, and status strip all
    // live on the same dark plate instead of floating on the node body.
    const root = document.createElement("div");
    root.className = "erpk-region-editor";
    root.style.position = "relative";
    root.style.display = "flex";
    root.style.flexDirection = "column";
    root.style.gap = "4px";
    root.style.padding = "6px";
    root.style.boxSizing = "border-box";
    root.style.width = "100%";
    root.style.height = "100%";
    root.style.minHeight = "160px";
    root.style.overflow = "hidden";
    root.style.background = PANEL_BG;
    root.style.border = "1px solid rgba(255, 255, 255, 0.08)";
    root.style.borderRadius = "6px";

    const stage = document.createElement("div");
    stage.className = "erpk-region-stage";
    stage.style.flex = "1 1 0";
    stage.style.minHeight = "0";
    stage.style.display = "flex";
    stage.style.alignItems = "center";
    stage.style.justifyContent = "center";
    stage.style.overflow = "hidden";

    const canvas = document.createElement("canvas");
    canvas.tabIndex = 0;
    canvas.style.outline = "none";
    canvas.style.background = STAGE_BG;
    canvas.style.border = "1px solid " + HAIRLINE;
    canvas.style.boxSizing = "border-box";
    canvas.style.borderRadius = "4px";
    canvas.style.touchAction = "none";
    canvas.style.cursor = "crosshair";
    stage.appendChild(canvas);

    // Camera-HUD strip: region count and selection on the left, frame
    // dimensions and reduced aspect ratio on the right.
    const status = document.createElement("div");
    status.className = "erpk-region-status";
    status.style.flex = "0 0 auto";
    status.style.height = STATUS_STRIP_H + "px";
    status.style.display = "flex";
    status.style.alignItems = "center";
    status.style.justifyContent = "space-between";
    status.style.gap = "8px";
    status.style.padding = "0";
    status.style.boxSizing = "border-box";
    status.style.font = "10px ui-monospace, Menlo, monospace";
    status.style.color = "rgba(255, 255, 255, 0.65)";
    status.style.whiteSpace = "nowrap";
    status.style.overflow = "hidden";

    const statusLeft = document.createElement("span");
    statusLeft.style.flex = "1 1 auto";
    statusLeft.style.minWidth = "0";
    statusLeft.style.overflow = "hidden";
    statusLeft.style.textOverflow = "ellipsis";
    const statusRight = document.createElement("span");
    statusRight.style.flex = "0 1 auto";
    statusRight.style.minWidth = "0";
    statusRight.style.overflow = "hidden";
    statusRight.style.fontVariantNumeric = "tabular-nums";
    function makeStripButton(label) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.classList.add("erpk-strip-btn");
        btn.textContent = label;
        btn.style.flex = "0 0 auto";
        btn.style.font = "inherit";
        btn.style.fontSize = "12px";
        btn.style.lineHeight = "1";
        btn.style.color = "rgba(255, 255, 255, 0.65)";
        btn.style.background = "transparent";
        btn.style.border = "1px solid rgba(255, 255, 255, 0.14)";
        btn.style.borderRadius = "3px";
        btn.style.padding = "1px 7px";
        btn.style.cursor = "pointer";
        return btn;
    }

    const gridBtn = makeStripButton("⊞");
    gridBtn.title = "Show grid";
    const gridSizeInput = document.createElement("input");
    gridSizeInput.type = "number";
    gridSizeInput.min = String(GRID_MIN_CELL_PX);
    gridSizeInput.max = String(GRID_MAX_CELL_PX);
    gridSizeInput.title = "Grid cell size in frame pixels (8–1024)";
    styleInput(gridSizeInput);
    gridSizeInput.style.width = "48px";
    gridSizeInput.style.flex = "0 0 auto";
    gridSizeInput.style.padding = "1px 4px";
    gridSizeInput.style.fontSize = "10px";
    gridSizeInput.style.display = "none";
    const gridColorInput = document.createElement("input");
    gridColorInput.type = "color";
    gridColorInput.value = GRID_DEFAULT_COLOR;
    gridColorInput.title = "Grid color";
    gridColorInput.style.flex = "0 0 auto";
    gridColorInput.style.width = "22px";
    gridColorInput.style.height = "18px";
    gridColorInput.style.alignSelf = "center";
    gridColorInput.style.padding = "0";
    gridColorInput.style.border = "1px solid rgba(255, 255, 255, 0.14)";
    gridColorInput.style.borderRadius = "3px";
    gridColorInput.style.background = "transparent";
    gridColorInput.style.cursor = "pointer";
    gridColorInput.style.display = "none";
    const gridAlphaInput = document.createElement("input");
    gridAlphaInput.type = "number";
    gridAlphaInput.min = "5";
    gridAlphaInput.max = "100";
    gridAlphaInput.title = "Grid opacity in percent (5–100)";
    styleInput(gridAlphaInput);
    gridAlphaInput.style.width = "40px";
    gridAlphaInput.style.flex = "0 0 auto";
    gridAlphaInput.style.padding = "1px 4px";
    gridAlphaInput.style.fontSize = "10px";
    gridAlphaInput.style.display = "none";
    const snapBtn = makeStripButton("⌖");
    snapBtn.title = "Snap drawing, moving, and resizing to the grid";
    const helpBtn = makeStripButton("?");
    helpBtn.title = "Drag to draw · Ctrl-drag force-draw · click select · "
        + "shift-click toggle · shift-drag marquee · drag moves selection · "
        + "Alt-click cycles overlap · double-click edits · right-click region list · "
        + "Del removes selected · Ctrl/Cmd+C/V/D copy/paste/duplicate · "
        + "[ ] depth · H hide boxes";
    const clearBtn = makeStripButton("Clear all");
    clearBtn.classList.add("erpk-btn-danger");
    clearBtn.title = "Remove every region (click twice to confirm)";
    clearBtn.style.font = "bold 9px 'Segoe UI', sans-serif";
    clearBtn.style.color = DANGER_RED_DIM;
    clearBtn.style.borderColor = DANGER_RED_BORDER;
    status.appendChild(statusLeft);
    status.appendChild(statusRight);
    status.appendChild(gridBtn);
    status.appendChild(gridSizeInput);
    status.appendChild(gridColorInput);
    status.appendChild(gridAlphaInput);
    status.appendChild(snapBtn);
    status.appendChild(helpBtn);
    status.appendChild(clearBtn);

    root.appendChild(stage);
    root.appendChild(status);

    const ctx = canvas.getContext("2d");

    // --- Inspector: edits the selected region in place -----------------
    const inspector = document.createElement("div");
    inspector.className = "erpk-region-inspector";
    inspector.style.flex = "0 0 auto";
    inspector.style.height = INSPECTOR_H + "px";
    inspector.style.display = "flex";
    inspector.style.alignItems = "stretch";
    inspector.style.gap = "6px";

    const descInput = document.createElement("input");
    descInput.type = "text";
    descInput.placeholder = "description — e.g. a red vintage car";
    descInput.title = "Description of the selected region";
    styleInput(descInput);
    descInput.style.width = "";
    descInput.style.flex = "2 1 0";
    descInput.style.minWidth = "0";

    const kindSelect = document.createElement("select");
    for (const kind of ["object", "text"]) {
        const option = document.createElement("option");
        option.value = kind;
        option.textContent = kind;
        kindSelect.appendChild(option);
    }
    kindSelect.title = "Region kind: an object in the scene, or literal text to render";
    styleInput(kindSelect);
    kindSelect.style.width = "";
    kindSelect.style.flex = "0 0 auto";

    const textInput = document.createElement("input");
    textInput.type = "text";
    textInput.placeholder = "text to render";
    textInput.title = "Literal text the model should render inside this region";
    styleInput(textInput);
    textInput.style.width = "";
    textInput.style.flex = "1 1 0";
    textInput.style.minWidth = "0";

    const plugBtn = makeStripButton("⌁");
    plugBtn.title = "Expose this region's description as an input";
    const backBtn = makeStripButton("▼");
    backBtn.title = "Send back — one layer toward the background ( [ )";
    const frontBtn = makeStripButton("▲");
    frontBtn.title = "Bring forward — one layer toward the front ( ] )";

    inspector.appendChild(descInput);
    inspector.appendChild(kindSelect);
    inspector.appendChild(textInput);
    inspector.appendChild(plugBtn);
    inspector.appendChild(backBtn);
    inspector.appendChild(frontBtn);
    root.insertBefore(inspector, status);

    // --- Widget plumbing ----------------------------------------------
    function syncWidget() {
        const widget = findWidget(node, "regions_data");
        if (widget) widget.value = serializeRegions(state.boxes);
        node.setDirtyCanvas?.(true, true);
    }

    function loadFromWidget() {
        const widget = findWidget(node, "regions_data");
        state.boxes = parseRegions(widget?.value ?? "[]");
        clearSelection();
        render();
    }

    function hideRegionsWidget() {
        const widget = findWidget(node, "regions_data");
        if (!widget || widget._erpkHidden) return;
        widget._erpkHidden = true;
        setWidgetHidden(widget, true);
        widget.computeSize = () => [0, -4];
        // Multiline string widgets carry their own DOM element depending on
        // the renderer; hide whichever is present so no textarea peeks through.
        if (widget.inputEl) widget.inputEl.style.display = "none";
        if (widget.element) widget.element.style.display = "none";
    }

    // A frame-aspect change can need more node height than the current size
    // provides; grow the node first so layout() sees the final stage size.
    function applyAspectChange() {
        const computed = node.computeSize?.();
        if (computed && node.size[1] < computed[1] - 1) {
            node.setSize([node.size[0], computed[1]]);
        }
        layout();
    }

    function hookDimensionWidget(name) {
        const widget = findWidget(node, name);
        if (!widget || widget._erpkAspectHooked) return;
        widget._erpkAspectHooked = true;
        const original = widget.callback;
        widget.callback = function () {
            const r = original?.apply(this, arguments);
            applyAspectChange();
            return r;
        };
        // Programmatic writes (widget.value = ...) bypass the callback, so the
        // value property relays them to applyAspectChange() as well.
        let currentValue = widget.value;
        Object.defineProperty(widget, "value", {
            get() { return currentValue; },
            set(v) {
                currentValue = v;
                applyAspectChange();
            },
            configurable: true,
            enumerable: true,
        });
    }

    // --- Layout & rendering --------------------------------------------
    function layout() {
        const availW = stage.clientWidth - STAGE_PADDING_PX;
        const availH = stage.clientHeight - STAGE_PADDING_PX;
        if (availW <= 0 || availH <= 0) return;
        // Width is authoritative: the canvas always spans the stage, and its
        // height follows the frame aspect (availH only trims rounding slack,
        // since the widget height is pinned to this same geometry).
        const aspect = frameAspect(node);
        const cw = availW;
        const ch = Math.min(cw / aspect, availH);
        const dpr = window.devicePixelRatio || 1;
        state.cssW = cw;
        state.cssH = ch;
        canvas.style.width = cw + "px";
        canvas.style.height = ch + "px";
        canvas.width = Math.max(1, Math.round(cw * dpr));
        canvas.height = Math.max(1, Math.round(ch * dpr));
        render();
    }

    function truncateLabel(text, maxWidth) {
        if (ctx.measureText(text).width <= maxWidth) return text;
        let t = text;
        while (t.length > 1 && ctx.measureText(t + "…").width > maxWidth) {
            t = t.slice(0, -1);
        }
        return t + "…";
    }

    function cornerHandles(box) {
        const x = box.x * state.cssW;
        const y = box.y * state.cssH;
        const w = box.w * state.cssW;
        const h = box.h * state.cssH;
        return [
            { id: "nw", px: x, py: y },
            { id: "ne", px: x + w, py: y },
            { id: "sw", px: x, py: y + h },
            { id: "se", px: x + w, py: y + h },
        ];
    }

    function drawBox(box, index) {
        const x = box.x * state.cssW;
        const y = box.y * state.cssH;
        const w = box.w * state.cssW;
        const h = box.h * state.cssH;
        const color = regionColor(index);
        const isSelected = state.selection.has(box);

        ctx.fillStyle = color + (isSelected ? "2e" : "17");
        ctx.fillRect(x, y, w, h);

        // Discrete diagonal hatching gives the fill a taped-off read.
        ctx.save();
        ctx.beginPath();
        ctx.rect(x, y, w, h);
        ctx.clip();
        ctx.strokeStyle = color + (isSelected ? "2c" : "18");
        ctx.lineWidth = 1;
        ctx.beginPath();
        for (let d = -h; d < w; d += 9) {
            ctx.moveTo(x + d, y + h);
            ctx.lineTo(x + d + h, y);
        }
        ctx.stroke();
        ctx.restore();

        ctx.strokeStyle = color;
        ctx.lineWidth = isSelected ? 2 : 1.5;
        ctx.strokeRect(x, y, w, h);

        // Text regions preview their literal text like a signage mock.
        if (box.kind === "text" && box.text) {
            ctx.save();
            ctx.beginPath();
            ctx.rect(x, y, w, h);
            ctx.clip();
            ctx.font = "13px 'Segoe UI', sans-serif";
            ctx.fillStyle = color;
            ctx.textAlign = "center";
            ctx.fillText(box.text, x + w / 2, y + h / 2 + 4, Math.max(w - 8, 10));
            ctx.restore();
            ctx.textAlign = "left";
        }

        // Numbered tape tag in the region's hue, a plug chip when the
        // description is wired from a desc_N input, description alongside.
        const tag = String(index + 1);
        ctx.font = "bold 9px 'Segoe UI', sans-serif";
        const tagW = Math.ceil(ctx.measureText(tag).width) + 7;
        ctx.fillStyle = color;
        ctx.fillRect(x, y, tagW, 13);
        ctx.fillStyle = "#fff";
        ctx.fillText(tag, x + 3.5, y + 9.5);
        let labelX = x + tagW;
        if (descWiredFor(box)) {
            const plugW = Math.ceil(ctx.measureText("⌁").width) + 7;
            ctx.fillStyle = color;
            ctx.fillRect(labelX + 1, y, plugW, 13);
            ctx.fillStyle = "#fff";
            ctx.fillText("⌁", labelX + 4.5, y + 9.5);
            labelX += plugW + 1;
        }
        if (box.desc) {
            ctx.font = LABEL_FONT;
            const label = truncateLabel(box.desc, Math.max(w - (labelX - x) - 28, 12));
            const labelWidth = ctx.measureText(label).width;
            ctx.fillStyle = "rgba(8, 8, 10, 0.72)";
            ctx.fillRect(labelX, y, labelWidth + 10, 13);
            ctx.fillStyle = "rgba(255, 255, 255, 0.92)";
            ctx.fillText(label, labelX + 5, y + 10);
        }

        if (box.kind === "text") {
            ctx.font = LABEL_FONT;
            const bx = x + w - 16;
            ctx.fillStyle = color;
            ctx.fillRect(bx, y + h - 16, 14, 14);
            ctx.fillStyle = INK_ON_TAPE;
            ctx.fillText("T", bx + 4, y + h - 5);
        }

        // Corner handles only resolve to one box, so they only show for a
        // single-region selection.
        if (isSelected && state.selection.size === 1) {
            for (const handle of cornerHandles(box)) {
                ctx.fillStyle = "#fff";
                ctx.fillRect(
                    handle.px - HANDLE_DRAW_PX / 2,
                    handle.py - HANDLE_DRAW_PX / 2,
                    HANDLE_DRAW_PX,
                    HANDLE_DRAW_PX,
                );
                ctx.strokeStyle = color;
                ctx.lineWidth = 1;
                ctx.strokeRect(
                    handle.px - HANDLE_DRAW_PX / 2,
                    handle.py - HANDLE_DRAW_PX / 2,
                    HANDLE_DRAW_PX,
                    HANDLE_DRAW_PX,
                );
            }
        }
    }

    function drawPending() {
        const rect = rectFrom(state.drag.anchor, state.drag.current);
        ctx.setLineDash([4, 3]);
        ctx.strokeStyle = "rgba(255, 255, 255, 0.5)";
        ctx.lineWidth = 1;
        ctx.strokeRect(
            rect.x * state.cssW,
            rect.y * state.cssH,
            rect.w * state.cssW,
            rect.h * state.cssH,
        );
        ctx.setLineDash([]);
    }

    function snapAxis(v, framePx) {
        if (!(state.gridShow && state.snapOn)) return v;
        const cell = state.gridCellPx;
        return clamp((Math.round((v * framePx) / cell) * cell) / framePx, 0, 1);
    }

    function snapPoint(p) {
        const dims = frameDims(node);
        return { x: snapAxis(p.x, dims.w), y: snapAxis(p.y, dims.h) };
    }

    // Draws the upstream image (LoadImage and executed preview nodes expose it
    // client-side via node.imgs) stretched to the frame; a distorted reference
    // is the cue that width/height do not match the source image.
    function drawReference() {
        const input = node.inputs?.find((i) => i.name === "image");
        if (!input || input.link == null) return false;
        const link = node.graph?.links?.[input.link];
        const origin = link ? node.graph.getNodeById(link.origin_id) : null;
        const img = origin?.imgs?.[0];
        if (!img) return false;
        if (!img.complete || !img.naturalWidth) {
            img.addEventListener("load", () => render(), { once: true });
            return false;
        }
        ctx.globalAlpha = 0.9;
        ctx.drawImage(img, 0, 0, state.cssW, state.cssH);
        ctx.globalAlpha = 1;
        return true;
    }

    function drawGrid() {
        if (!state.gridShow) return;
        const dims = frameDims(node);
        const cell = state.gridCellPx;
        ctx.strokeStyle = hexToRgba(state.gridColor, state.gridAlpha);
        ctx.lineWidth = 1;
        ctx.beginPath();
        for (let px = cell; px < dims.w; px += cell) {
            const x = (px / dims.w) * state.cssW;
            ctx.moveTo(x, 0);
            ctx.lineTo(x, state.cssH);
        }
        for (let px = cell; px < dims.h; px += cell) {
            const y = (px / dims.h) * state.cssH;
            ctx.moveTo(0, y);
            ctx.lineTo(state.cssW, y);
        }
        ctx.stroke();
    }

    // Rule-of-thirds hairlines double as a placement reference for the 3x3
    // verbal grid the Python side derives placements from.
    function drawGuides() {
        ctx.strokeStyle = HAIRLINE;
        ctx.lineWidth = 1;
        for (const f of [1 / 3, 2 / 3]) {
            ctx.beginPath();
            ctx.moveTo(f * state.cssW, 0);
            ctx.lineTo(f * state.cssW, state.cssH);
            ctx.moveTo(0, f * state.cssH);
            ctx.lineTo(state.cssW, f * state.cssH);
            ctx.stroke();
        }
    }

    // Empty frame reads like an unrecorded viewfinder: center crosshair
    // with the interaction hint beneath it.
    function drawEmptyHint() {
        const cx = state.cssW / 2;
        const cy = state.cssH / 2;
        ctx.strokeStyle = HAIRLINE_STRONG;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(cx - 9, cy);
        ctx.lineTo(cx + 9, cy);
        ctx.moveTo(cx, cy - 9);
        ctx.lineTo(cx, cy + 9);
        ctx.stroke();
        ctx.font = LABEL_FONT;
        ctx.textAlign = "center";
        ctx.fillStyle = "rgba(255, 255, 255, 0.45)";
        ctx.fillText("Drag to block out a region", cx, cy + 28);
        ctx.fillStyle = "rgba(255, 255, 255, 0.28)";
        ctx.fillText("Right-click for the region list · ? in the bar for all shortcuts", cx, cy + 44);
        ctx.textAlign = "left";
    }

    function drawHiddenHint() {
        ctx.font = "10px ui-monospace, Menlo, monospace";
        ctx.fillStyle = "rgba(255, 255, 255, 0.45)";
        ctx.fillText("boxes hidden — H to show", 8, state.cssH - 8);
    }

    function ratioString(w, h) {
        const gcd = (a, b) => (b ? gcd(b, a % b) : a);
        const d = gcd(w, h) || 1;
        return `${Math.round(w / d)}:${Math.round(h / d)}`;
    }

    function renderStatus() {
        statusLeft.textContent = "";
        const count = state.boxes.length;
        const countSpan = document.createElement("span");
        countSpan.textContent = count === 0
            ? "No regions yet"
            : `${count} region${count === 1 ? "" : "s"}`;
        countSpan.style.color = count === 0
            ? "rgba(255, 255, 255, 0.4)"
            : "rgba(255, 255, 255, 0.65)";
        statusLeft.appendChild(countSpan);
        const index = primaryIndex();
        const box = index >= 0 ? state.boxes[index] : null;
        if (box) {
            const sel = document.createElement("span");
            const name = box.kind === "text"
                ? (box.text || box.desc || "text")
                : (box.desc || "unnamed");
            sel.textContent = ` · #${index + 1} ${name}`;
            sel.style.color = regionColor(index);
            statusLeft.appendChild(sel);
        }
        const w = Number(findWidget(node, "width")?.value) || 1024;
        const h = Number(findWidget(node, "height")?.value) || 1024;
        statusRight.textContent = `${w}×${h} · ${ratioString(w, h)}`;
        clearBtn.disabled = !count;
        clearBtn.style.opacity = count ? "1" : "0.45";
        clearBtn.style.cursor = count ? "pointer" : "default";
        if (!count) disarmClear();
        syncDescSockets();
        syncInspector();
    }

    function render() {
        if (!state.cssW || !state.cssH) return;
        const dpr = window.devicePixelRatio || 1;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.clearRect(0, 0, state.cssW, state.cssH);
        const hasReference = drawReference();
        drawGrid();
        drawGuides();
        if (!state.boxes.length && !state.drag && !hasReference) drawEmptyHint();
        if (state.hideBoxes) {
            drawHiddenHint();
        } else {
            state.boxes.forEach((box, i) => drawBox(box, i));
        }
        if (state.drag?.mode === "create" || state.drag?.mode === "marquee") drawPending();
        renderStatus();
        // Keyboard mutations (delete, paste, duplicate, depth) reach the open
        // panel through the shared render path; a row drag in flight owns the
        // row DOM and must not be rebuilt under the pointer.
        if (panel && !panelRowDragging) renderPanelRows();
    }

    // --- Hit testing -----------------------------------------------------
    function pointerNorm(e) {
        const r = canvas.getBoundingClientRect();
        if (!r.width || !r.height) return { x: 0, y: 0 };
        return {
            x: clamp((e.clientX - r.left) / r.width, 0, 1),
            y: clamp((e.clientY - r.top) / r.height, 0, 1),
        };
    }

    // Bounding-rect pixels are scaled by the graph zoom (the DOM widget wrapper
    // carries a CSS transform), so convert into layout CSS pixels before
    // comparing against handle positions derived from cssW/cssH.
    function pointerPx(e) {
        const r = canvas.getBoundingClientRect();
        if (!r.width || !r.height) return { px: -1, py: -1 };
        return {
            px: (e.clientX - r.left) * (state.cssW / r.width),
            py: (e.clientY - r.top) * (state.cssH / r.height),
        };
    }

    function hitHandle(pp) {
        if (state.hideBoxes || state.selection.size !== 1) return null;
        const box = state.primary;
        if (!box) return null;
        for (const handle of cornerHandles(box)) {
            if (
                Math.abs(pp.px - handle.px) <= HANDLE_HIT_PX
                && Math.abs(pp.py - handle.py) <= HANDLE_HIT_PX
            ) {
                return handle.id;
            }
        }
        return null;
    }

    // Every box under the pointer, topmost first: later boxes draw above
    // earlier ones.
    function boxesAt(p) {
        const hits = [];
        for (let i = state.boxes.length - 1; i >= 0; i--) {
            const b = state.boxes[i];
            if (p.x >= b.x && p.x <= b.x + b.w && p.y >= b.y && p.y <= b.y + b.h) {
                hits.push(b);
            }
        }
        return hits;
    }

    // Topmost box wins.
    function hitBox(p) {
        if (state.hideBoxes) return -1;
        const hits = boxesAt(p);
        return hits.length ? state.boxes.indexOf(hits[0]) : -1;
    }

    function resizeAnchor(box, handleId) {
        if (handleId === "nw") return { x: box.x + box.w, y: box.y + box.h };
        if (handleId === "ne") return { x: box.x, y: box.y + box.h };
        if (handleId === "sw") return { x: box.x + box.w, y: box.y };
        return { x: box.x, y: box.y };
    }

    function updateCursor(e) {
        if (state.hideBoxes) {
            canvas.style.cursor = "crosshair";
            return;
        }
        const handleId = hitHandle(pointerPx(e));
        if (handleId) {
            canvas.style.cursor =
                handleId === "nw" || handleId === "se" ? "nwse-resize" : "nesw-resize";
            return;
        }
        const hit = hitBox(pointerNorm(e));
        if (hit >= 0 && state.selection.has(state.boxes[hit])) {
            canvas.style.cursor = "move";
        } else if (hit >= 0) {
            canvas.style.cursor = "pointer";
        } else {
            canvas.style.cursor = "crosshair";
        }
    }

    // --- Selection -----------------------------------------------------
    // Selection tracks region objects, not indices, so membership and the
    // primary survive depth reorders the same way the inspector binding does.
    function primaryIndex() {
        return state.primary ? state.boxes.indexOf(state.primary) : -1;
    }

    function lastSelected() {
        let last = null;
        for (const box of state.selection) last = box;
        return last;
    }

    function select(box, { toggle = false } = {}) {
        if (toggle) {
            if (state.selection.has(box)) {
                state.selection.delete(box);
                if (state.primary === box) state.primary = lastSelected();
            } else {
                state.selection.add(box);
                state.primary = box;
            }
        } else {
            state.selection = new Set([box]);
            state.primary = box;
        }
    }

    function clearSelection() {
        state.selection.clear();
        state.primary = null;
    }

    // Selected regions in array (depth) order, backmost first.
    function selectionInOrder() {
        return state.boxes.filter((b) => state.selection.has(b));
    }

    function deleteSelected() {
        if (!state.selection.size) return;
        state.boxes = state.boxes.filter((b) => !state.selection.has(b));
        clearSelection();
        syncWidget();
        render();
    }

    // Appends clones of the given regions on top (frontmost), nudged so the
    // copies read as distinct from their sources, and selects them.
    function pasteRegions(source) {
        if (!source.length) return;
        const pasted = source.map((b) => ({
            ...b,
            x: clamp(b.x + 0.02, 0, 1 - b.w),
            y: clamp(b.y + 0.02, 0, 1 - b.h),
        }));
        state.boxes.push(...pasted);
        state.selection = new Set(pasted);
        state.primary = pasted[pasted.length - 1];
        syncWidget();
        render();
    }

    // --- Inspector flow ----------------------------------------------------
    // Repopulate only when the selected region object changes, so the render
    // loop never clobbers live typing or resets the cursor.
    let inspected = null;

    // A connected desc_N socket owns that region's description; the field
    // locks so typed text never silently loses to the wire at execute time.
    function descWiredFor(box) {
        const index = state.boxes.indexOf(box);
        if (index < 0) return false;
        const input = node.inputs?.find((i) => i.name === `desc_${index + 1}`);
        return input?.link != null;
    }

    function exposedDescSet() {
        const saved = node.properties?.erpk_region_desc;
        return new Set(Array.isArray(saved) ? saved : []);
    }

    function persistExposedDesc(set) {
        if (!node.properties) node.properties = {};
        node.properties.erpk_region_desc = [...set].sort((a, b) => a - b);
    }

    // The node face only carries desc sockets that are exposed or wired. The
    // Vue renderer ignores input.hidden, so unexposed sockets are physically
    // removed and re-added on demand (removeInput fixes up link slot indices;
    // wired sockets are never removed). Labels carry the region's text so a
    // depth reorder visibly remaps the wires.
    function syncDescSockets() {
        if (!node.inputs) return;
        const exposed = exposedDescSet();
        let changed = false;
        for (const input of node.inputs) {
            const match = input.name?.match(/^desc_(\d+)$/);
            if (match && input.link != null && !exposed.has(+match[1])) {
                exposed.add(+match[1]);
                changed = true;
            }
        }
        for (let i = node.inputs.length - 1; i >= 0; i--) {
            const input = node.inputs[i];
            const match = input.name?.match(/^desc_(\d+)$/);
            if (match && !exposed.has(+match[1]) && input.link == null) {
                node.removeInput(i);
            }
        }
        for (const n of [...exposed].sort((a, b) => a - b)) {
            if (n < 1 || n > REGION_DESC_INPUTS) continue;
            if (!node.inputs.some((i) => i.name === `desc_${n}`)) {
                node.addInput(`desc_${n}`, "STRING");
            }
        }
        for (const input of node.inputs) {
            const match = input.name?.match(/^desc_(\d+)$/);
            if (!match) continue;
            const n = +match[1];
            const box = state.boxes[n - 1];
            const text = box ? (box.desc || box.text || `region ${n}`) : "unused";
            input.label = `desc ${n} · ${text.length > 18 ? text.slice(0, 17) + "…" : text}`;
        }
        if (changed) persistExposedDesc(exposed);
        const computed = node.computeSize?.();
        if (computed && node.size[1] < computed[1]) {
            node.setSize([node.size[0], computed[1]]);
        }
    }

    function onPlugToggle() {
        const index = primaryIndex();
        if (index < 0 || index >= REGION_DESC_INPUTS) return;
        if (descWiredFor(state.primary)) return;
        const n = index + 1;
        const exposed = exposedDescSet();
        if (exposed.has(n)) exposed.delete(n);
        else exposed.add(n);
        persistExposedDesc(exposed);
        syncDescSockets();
        node.setDirtyCanvas?.(true, true);
        render();
    }

    function syncInspector() {
        const box = state.primary;
        const showText = !!box && box.kind === "text";
        textInput.style.display = showText ? "" : "none";
        textInput.disabled = !showText;
        const wired = !!box && descWiredFor(box);
        descInput.disabled = !box || wired;
        descInput.placeholder = wired
            ? `wired from the desc_${state.boxes.indexOf(box) + 1} input`
            : "description — e.g. a red vintage car";
        const index = box ? state.boxes.indexOf(box) : -1;
        const wireable = index >= 0 && index < REGION_DESC_INPUTS;
        const plugged = wireable && (wired || exposedDescSet().has(index + 1));
        plugBtn.disabled = !wireable || wired;
        plugBtn.style.opacity = wireable ? "1" : "0.45";
        plugBtn.style.color = plugged
            ? "rgba(255, 255, 255, 0.92)" : "rgba(255, 255, 255, 0.65)";
        plugBtn.style.borderColor = plugged
            ? "rgba(255, 255, 255, 0.45)" : "rgba(255, 255, 255, 0.14)";
        plugBtn.title = wired
            ? "Description is wired — disconnect the input to unplug"
            : plugged
                ? "Hide this region's description input"
                : wireable
                    ? "Expose this region's description as an input"
                    : "Only regions 1–6 can take a description input";
        if (box === inspected) return;
        inspected = box;
        descInput.value = box ? box.desc : "";
        kindSelect.value = box ? box.kind : "object";
        textInput.value = box ? box.text : "";
        kindSelect.disabled = !box;
        backBtn.disabled = !box;
        frontBtn.disabled = !box;
        const dim = box ? "1" : "0.45";
        backBtn.style.opacity = dim;
        frontBtn.style.opacity = dim;
    }

    // Array order is depth: index 0 is backmost, the last region is frontmost.
    // Draw order, hit-testing, numbering, and the prompt's back-to-front
    // element list all follow it. Returns the region's new index.
    function moveRegion(index, delta) {
        const target = index + delta;
        if (index < 0 || target < 0 || target >= state.boxes.length) return index;
        const [box] = state.boxes.splice(index, 1);
        state.boxes.splice(target, 0, box);
        syncWidget();
        return target;
    }

    function moveSelectedRegion(delta) {
        const index = primaryIndex();
        if (index < 0) return;
        moveRegion(index, delta);
        render();
    }

    // --- Event handlers ----------------------------------------------------
    function onPointerDown(e) {
        if (e.button !== 0) return;
        e.stopPropagation();
        canvas.focus();
        canvas.setPointerCapture(e.pointerId);

        const p = pointerNorm(e);

        // Ctrl/Cmd forces a fresh box even when the drag starts over one.
        if (e.ctrlKey || e.metaKey) {
            clearSelection();
            const anchor = snapPoint(p);
            state.drag = { mode: "create", anchor, current: anchor };
            render();
            return;
        }

        // Shift toggles membership on a box, or starts a marquee on empty
        // canvas.
        if (e.shiftKey) {
            const hit = hitBox(p);
            if (hit >= 0) {
                select(state.boxes[hit], { toggle: true });
            } else {
                state.drag = { mode: "marquee", anchor: p, current: p };
            }
            render();
            return;
        }

        // Alt cycles through the stack under the pointer, topmost first;
        // with nothing underneath it falls through to the plain behavior.
        if (e.altKey && !state.hideBoxes) {
            const hits = boxesAt(p);
            if (hits.length) {
                const idx = hits.indexOf(state.primary);
                select(hits[(idx + 1) % hits.length]);
                render();
                return;
            }
        }

        const handleId = hitHandle(pointerPx(e));
        if (handleId) {
            const box = state.primary;
            state.drag = { mode: "resize", box, anchor: resizeAnchor(box, handleId) };
        } else {
            const hit = hitBox(p);
            if (hit >= 0) {
                const box = state.boxes[hit];
                const wasSelected = state.selection.has(box);
                if (wasSelected) {
                    state.primary = box;
                } else {
                    select(box);
                }
                state.drag = {
                    mode: "move",
                    grabDX: p.x - box.x,
                    grabDY: p.y - box.y,
                    startX: box.x,
                    startY: box.y,
                    starts: new Map(
                        [...state.selection].map((b) => [b, { x: b.x, y: b.y }]),
                    ),
                    moved: false,
                    // A plain click (no movement) inside a multi-selection
                    // collapses to just that box on release.
                    collapseTo: wasSelected && state.selection.size > 1 ? box : null,
                };
            } else {
                clearSelection();
                const anchor = snapPoint(p);
                state.drag = { mode: "create", anchor, current: anchor };
            }
        }
        render();
    }

    function onPointerMove(e) {
        if (!state.drag) {
            updateCursor(e);
            return;
        }
        const p = pointerNorm(e);
        const d = state.drag;
        if (d.mode === "create") {
            d.current = snapPoint(p);
        } else if (d.mode === "marquee") {
            d.current = p;
        } else if (d.mode === "move") {
            // Snap resolves on the grabbed (primary) box; the rest of the
            // selection follows the same delta, each clamping individually.
            const box = state.primary;
            if (!box) return;
            const dims = frameDims(node);
            const dx = clamp(snapAxis(p.x - d.grabDX, dims.w), 0, 1 - box.w) - d.startX;
            const dy = clamp(snapAxis(p.y - d.grabDY, dims.h), 0, 1 - box.h) - d.startY;
            if (dx || dy) d.moved = true;
            for (const [b, start] of d.starts) {
                b.x = clamp(start.x + dx, 0, 1 - b.w);
                b.y = clamp(start.y + dy, 0, 1 - b.h);
            }
        } else if (d.mode === "resize") {
            if (!d.box) return;
            Object.assign(d.box, rectFrom(d.anchor, snapPoint(p)));
        }
        render();
    }

    function onPointerUp(e) {
        if (!state.drag) return;
        if (canvas.hasPointerCapture?.(e.pointerId)) {
            canvas.releasePointerCapture(e.pointerId);
        }
        const d = state.drag;
        state.drag = null;

        if (d.mode === "create") {
            const rect = rectFrom(d.anchor, d.current);
            if (rect.w >= MIN_REGION_SIZE && rect.h >= MIN_REGION_SIZE) {
                const box = { ...rect, kind: "object", desc: "", text: "" };
                state.boxes.push(box);
                select(box);
                syncWidget();
            }
        } else if (d.mode === "marquee") {
            const rect = rectFrom(d.anchor, d.current);
            const hits = state.boxes.filter((b) =>
                b.x <= rect.x + rect.w && b.x + b.w >= rect.x
                && b.y <= rect.y + rect.h && b.y + b.h >= rect.y);
            state.selection = new Set(hits);
            state.primary = hits.length ? hits[hits.length - 1] : null;
        } else if (d.mode === "move") {
            if (!d.moved && d.collapseTo) {
                select(d.collapseTo);
            } else {
                for (const box of d.starts.keys()) enforceMinSize(box);
                syncWidget();
            }
        } else if (d.mode === "resize") {
            if (d.box) {
                enforceMinSize(d.box);
                syncWidget();
            }
        }
        render();
    }

    function onDblClick(e) {
        e.stopPropagation();
        const hit = hitBox(pointerNorm(e));
        if (hit < 0) return;
        select(state.boxes[hit]);
        render();
        descInput.focus();
        descInput.select();
    }

    function onKeyDown(e) {
        const mod = e.ctrlKey || e.metaKey;
        const key = e.key.toLowerCase();
        if (
            (e.key === "Delete" || e.key === "Backspace")
            && state.selection.size
        ) {
            e.preventDefault();
            e.stopPropagation();
            deleteSelected();
            return;
        }
        if ((e.key === "[" || e.key === "]") && state.primary) {
            e.preventDefault();
            e.stopPropagation();
            moveSelectedRegion(e.key === "]" ? 1 : -1);
            return;
        }
        if (mod && key === "c" && state.selection.size) {
            e.preventDefault();
            e.stopPropagation();
            regionClipboard = selectionInOrder().map((b) => ({ ...b }));
            return;
        }
        if (mod && key === "v" && regionClipboard.length) {
            e.preventDefault();
            e.stopPropagation();
            pasteRegions(regionClipboard);
            return;
        }
        // Always swallowed so the browser bookmark dialog never fires.
        if (mod && key === "d") {
            e.preventDefault();
            e.stopPropagation();
            if (state.selection.size) pasteRegions(selectionInOrder());
            return;
        }
        if (key === "h" && !mod && !e.altKey && !e.shiftKey) {
            e.preventDefault();
            e.stopPropagation();
            state.hideBoxes = !state.hideBoxes;
            render();
        }
    }

    function onInspectorPointerDown(e) {
        e.stopPropagation();
    }

    // Keep typing out of ComfyUI's global hotkeys and the canvas handlers.
    function onInspectorKeyDown(e) {
        e.stopPropagation();
        if (e.key === "Enter") {
            e.preventDefault();
            e.target.blur?.();
        }
    }

    function onDescInput() {
        const box = state.primary;
        if (!box) return;
        box.desc = descInput.value;
        syncWidget();
        render();
    }

    function onKindChange() {
        const box = state.primary;
        if (!box) return;
        box.kind = kindSelect.value === "text" ? "text" : "object";
        syncWidget();
        render();
        if (box.kind === "text") textInput.focus();
    }

    function onTextInput() {
        const box = state.primary;
        if (!box) return;
        box.text = textInput.value;
        syncWidget();
        render();
    }

    // Grid/snap are editor preferences, persisted through node.properties so
    // they travel with the workflow without touching the widget schema.
    function persistGridPrefs() {
        if (!node.properties) node.properties = {};
        node.properties.erpk_region_grid = {
            on: state.gridShow,
            cell: state.gridCellPx,
            color: state.gridColor,
            alpha: state.gridAlpha,
            snap: state.snapOn,
        };
    }

    // Tolerates the earlier stored shapes: {grid: bool} and {divs: number}
    // (cells per axis, 0 meant off) - divisions convert via the frame width.
    function restoreGridPrefs() {
        const saved = node.properties?.erpk_region_grid;
        if (saved && typeof saved === "object") {
            if (Number.isFinite(saved.cell)) {
                state.gridCellPx = clamp(
                    Math.round(saved.cell), GRID_MIN_CELL_PX, GRID_MAX_CELL_PX);
            } else if (Number.isFinite(saved.divs) && saved.divs > 0) {
                state.gridCellPx = clamp(
                    Math.round(frameDims(node).w / saved.divs),
                    GRID_MIN_CELL_PX, GRID_MAX_CELL_PX);
            }
            if (typeof saved.color === "string" && /^#[0-9a-fA-F]{6}$/.test(saved.color)) {
                state.gridColor = saved.color;
            }
            if (Number.isFinite(saved.alpha)) {
                state.gridAlpha = clamp(saved.alpha, 0.05, 1);
            }
            state.gridShow = saved.on !== undefined
                ? !!saved.on
                : (Number.isFinite(saved.divs) ? saved.divs > 0 : !!saved.grid);
            state.snapOn = !!saved.snap;
        }
        syncToolButtons();
    }

    function syncToolButtons() {
        const on = "rgba(255, 255, 255, 0.92)";
        const off = "rgba(255, 255, 255, 0.65)";
        const onBorder = "rgba(255, 255, 255, 0.45)";
        const offBorder = "rgba(255, 255, 255, 0.14)";
        gridBtn.style.color = state.gridShow ? on : off;
        gridBtn.style.borderColor = state.gridShow ? onBorder : offBorder;
        gridSizeInput.style.display = state.gridShow ? "" : "none";
        gridColorInput.style.display = state.gridShow ? "" : "none";
        gridAlphaInput.style.display = state.gridShow ? "" : "none";
        if (document.activeElement !== gridSizeInput) {
            gridSizeInput.value = String(state.gridCellPx);
        }
        if (document.activeElement !== gridColorInput) {
            gridColorInput.value = state.gridColor;
        }
        if (document.activeElement !== gridAlphaInput) {
            gridAlphaInput.value = String(Math.round(state.gridAlpha * 100));
        }
        const snapActive = state.gridShow && state.snapOn;
        snapBtn.disabled = !state.gridShow;
        snapBtn.style.opacity = state.gridShow ? "1" : "0.45";
        snapBtn.style.cursor = state.gridShow ? "pointer" : "default";
        snapBtn.style.color = snapActive ? on : off;
        snapBtn.style.borderColor = snapActive ? onBorder : offBorder;
    }

    function onGridToggle() {
        state.gridShow = !state.gridShow;
        persistGridPrefs();
        syncToolButtons();
        render();
    }

    function onGridSizeInput() {
        const v = Math.round(Number(gridSizeInput.value));
        if (!Number.isFinite(v)) return;
        state.gridCellPx = clamp(v, GRID_MIN_CELL_PX, GRID_MAX_CELL_PX);
        persistGridPrefs();
        render();
    }

    function onGridSizeBlur() {
        gridSizeInput.value = String(state.gridCellPx);
    }

    function onGridColorInput() {
        state.gridColor = gridColorInput.value;
        persistGridPrefs();
        render();
    }

    function onGridAlphaInput() {
        const v = Math.round(Number(gridAlphaInput.value));
        if (!Number.isFinite(v)) return;
        state.gridAlpha = clamp(v, 5, 100) / 100;
        persistGridPrefs();
        render();
    }

    function onGridAlphaBlur() {
        gridAlphaInput.value = String(Math.round(state.gridAlpha * 100));
    }

    function onGridSizeKeyDown(e) {
        e.stopPropagation();
        if (e.key === "Enter") {
            e.preventDefault();
            gridSizeInput.blur();
        }
    }

    function onSnapToggle() {
        if (!state.gridShow) return;
        state.snapOn = !state.snapOn;
        persistGridPrefs();
        syncToolButtons();
        render();
    }

    // Two-step confirm keeps a stray click from nuking the layout without
    // resorting to a blocking dialog.
    let clearArm = null;

    function disarmClear() {
        if (clearArm) clearTimeout(clearArm);
        clearArm = null;
        clearBtn.textContent = "Clear all";
        clearBtn.style.color = DANGER_RED_DIM;
        clearBtn.style.borderColor = DANGER_RED_BORDER;
    }

    function onClearClick() {
        if (!state.boxes.length) return;
        if (clearArm === null) {
            clearBtn.textContent = "Confirm?";
            clearBtn.style.color = DANGER_RED;
            clearBtn.style.borderColor = DANGER_RED;
            clearArm = setTimeout(disarmClear, 2500);
            return;
        }
        disarmClear();
        state.boxes = [];
        clearSelection();
        syncWidget();
        render();
    }

    function onSendBack() {
        moveSelectedRegion(-1);
    }

    function onBringForward() {
        moveSelectedRegion(1);
    }

    // The help button is reference-only; eating the pointerdown keeps it
    // from stealing focus or reaching the graph.
    function onHelpPointerDown(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // --- Region list panel ----------------------------------------------
    // Right-click panel listing regions front-to-back with per-row select,
    // duplicate, delete, and pointer-drag depth reordering.
    let panel = null;
    let panelList = null;
    let panelRowDragging = false;

    // Pointer position in the root's layout pixels; the bounding rect is
    // scaled by the graph zoom, so divide it back out.
    function panelPoint(e) {
        const r = root.getBoundingClientRect();
        if (!r.width || !r.height) return { x: 0, y: 0 };
        return {
            x: (e.clientX - r.left) * (root.offsetWidth / r.width),
            y: (e.clientY - r.top) * (root.offsetHeight / r.height),
        };
    }

    function closePanel() {
        if (!panel) return;
        document.removeEventListener("pointerdown", onDocPointerDown, true);
        document.removeEventListener("keydown", onDocKeyDown, true);
        panel.remove();
        panel = null;
        panelList = null;
    }

    function onDocPointerDown(e) {
        if (!panel || panel.contains(e.target)) return;
        // Right-button presses on the canvas resolve through the contextmenu
        // toggle instead, so one gesture doesn't close and then reopen.
        if (e.button === 2 && e.target === canvas) return;
        closePanel();
    }

    function onDocKeyDown(e) {
        if (e.key === "Escape" && panel) {
            e.preventDefault();
            e.stopPropagation();
            closePanel();
        }
    }

    function onPanelPointerDown(e) {
        e.stopPropagation();
    }

    function onPanelContextMenu(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function duplicateRegion(box) {
        pasteRegions([box]);
        renderPanelRows();
    }

    function deleteRegion(box) {
        const index = state.boxes.indexOf(box);
        if (index < 0) return;
        state.boxes.splice(index, 1);
        state.selection.delete(box);
        if (state.primary === box) state.primary = lastSelected();
        syncWidget();
        render();
        if (state.boxes.length) renderPanelRows();
        else closePanel();
    }

    // Dropping commits the DOM order back into the array; the list displays
    // reversed, so the reorder reads bottom row = index 0 (backmost).
    function commitPanelOrder() {
        if (!panelList) return;
        const order = [...panelList.children].map((el) => el._erpkBox).reverse();
        // A keyboard mutation mid-drag invalidates the row snapshot; refuse a
        // reorder that would add or drop regions and just rebuild the list.
        const valid = order.length === state.boxes.length
            && order.every((box) => state.boxes.includes(box));
        if (valid) {
            state.boxes = order;
            syncWidget();
        }
        render();
        renderPanelRows();
    }

    // The drag listens on window for its lifetime (capture on a reparented
    // element is unreliable) and moves rows with transforms only: the grabbed
    // row follows the pointer, siblings glide aside with a short ease, and the
    // single DOM reorder happens on drop.
    function onRowPointerDown(e, row) {
        if (e.button !== 0) return;
        e.stopPropagation();
        e.preventDefault();
        const startY = e.clientY;
        let dragging = false;
        panelRowDragging = true;
        const rows = [...panelList.children];
        const startIndex = rows.indexOf(row);
        const rowH = row.offsetHeight;
        // Pointer deltas arrive in screen pixels; transforms apply in layout
        // pixels, and the graph zoom scales between the two.
        const zoom = row.getBoundingClientRect().height / rowH || 1;
        let targetIndex = startIndex;

        function onRowMove(ev) {
            if (!dragging && Math.abs(ev.clientY - startY) > 4) {
                dragging = true;
                row.style.opacity = "0.85";
                row.style.position = "relative";
                row.style.zIndex = "1";
                for (const el of rows) {
                    if (el !== row) el.style.transition = "transform 120ms ease";
                }
            }
            if (!dragging || !panelList) return;
            const dy = clamp(
                (ev.clientY - startY) / zoom,
                -startIndex * rowH,
                (rows.length - 1 - startIndex) * rowH,
            );
            row.style.transform = `translateY(${dy}px)`;
            targetIndex = clamp(startIndex + Math.round(dy / rowH), 0, rows.length - 1);
            rows.forEach((el, i) => {
                if (el === row) return;
                let shift = 0;
                if (startIndex < targetIndex && i > startIndex && i <= targetIndex) {
                    shift = -rowH;
                } else if (startIndex > targetIndex && i >= targetIndex && i < startIndex) {
                    shift = rowH;
                }
                el.style.transform = shift ? `translateY(${shift}px)` : "";
            });
        }

        function onRowUp() {
            window.removeEventListener("pointermove", onRowMove, true);
            window.removeEventListener("pointerup", onRowUp, true);
            window.removeEventListener("pointercancel", onRowUp, true);
            panelRowDragging = false;
            for (const el of rows) {
                el.style.transition = "";
                el.style.transform = "";
            }
            row.style.opacity = "";
            row.style.position = "";
            row.style.zIndex = "";
            if (dragging) {
                if (panelList && targetIndex !== startIndex) {
                    const ref = rows[targetIndex];
                    if (targetIndex > startIndex) {
                        panelList.insertBefore(row, ref.nextSibling);
                    } else {
                        panelList.insertBefore(row, ref);
                    }
                }
                commitPanelOrder();
            } else if (state.boxes.includes(row._erpkBox)) {
                select(row._erpkBox);
                render();
                renderPanelRows();
            } else {
                renderPanelRows();
            }
        }

        window.addEventListener("pointermove", onRowMove, true);
        window.addEventListener("pointerup", onRowUp, true);
        window.addEventListener("pointercancel", onRowUp, true);
    }

    function buildPanelRow(index) {
        const box = state.boxes[index];
        const row = document.createElement("div");
        row._erpkBox = box;
        row.className = "erpk-region-row";
        row.style.display = "flex";
        row.style.alignItems = "center";
        row.style.gap = "5px";
        row.style.padding = "2px 5px";
        row.style.borderRadius = "3px";
        row.style.cursor = "grab";
        row.style.border = "1px solid "
            + (state.selection.has(box) ? HAIRLINE_STRONG : "transparent");
        row.style.font = "8px 'Segoe UI', sans-serif";
        row.style.color = "rgba(255, 255, 255, 0.8)";

        const swatch = document.createElement("span");
        swatch.style.flex = "0 0 auto";
        swatch.style.width = "9px";
        swatch.style.height = "9px";
        swatch.style.borderRadius = "2px";
        swatch.style.background = regionColor(index);

        const num = document.createElement("span");
        num.style.flex = "0 0 auto";
        num.style.color = "rgba(255, 255, 255, 0.5)";
        num.style.fontVariantNumeric = "tabular-nums";
        num.textContent = String(index + 1).padStart(2, "0");

        const plug = document.createElement("span");
        plug.style.flex = "0 0 auto";
        plug.style.color = regionColor(index);
        plug.title = "Description wired from a desc input";
        plug.textContent = "⌁";
        plug.style.display = descWiredFor(box) ? "" : "none";

        const label = document.createElement("span");
        label.style.flex = "1 1 auto";
        label.style.minWidth = "0";
        label.style.overflow = "hidden";
        label.style.textOverflow = "ellipsis";
        label.style.whiteSpace = "nowrap";
        const text = box.kind === "text" ? box.text : box.desc;
        if (text) {
            label.textContent = text;
        } else {
            label.textContent = "(empty)";
            label.style.fontStyle = "italic";
            label.style.color = "rgba(255, 255, 255, 0.4)";
        }

        const dupBtn = makeStripButton("⧉");
        dupBtn.title = "Duplicate region";
        dupBtn.style.fontSize = "10px";
        dupBtn.style.padding = "0 4px";
        const delBtn = makeStripButton("✕");
        delBtn.classList.add("erpk-btn-danger");
        delBtn.title = "Delete region";
        delBtn.style.fontSize = "10px";
        delBtn.style.padding = "0 4px";
        delBtn.style.color = DANGER_RED_DIM;
        delBtn.style.borderColor = DANGER_RED_BORDER;

        row.appendChild(swatch);
        row.appendChild(num);
        row.appendChild(plug);
        row.appendChild(label);
        row.appendChild(dupBtn);
        row.appendChild(delBtn);

        // Button presses must not start a row drag; their listeners die with
        // the row element on rebuild or panel close.
        dupBtn.addEventListener("pointerdown", (e) => e.stopPropagation());
        delBtn.addEventListener("pointerdown", (e) => e.stopPropagation());
        dupBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            duplicateRegion(box);
        });
        delBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            deleteRegion(box);
        });
        row.addEventListener("pointerdown", (e) => onRowPointerDown(e, row));
        return row;
    }

    // Top row = frontmost region (the end of the array).
    function renderPanelRows() {
        if (!panelList) return;
        panelList.textContent = "";
        for (let i = state.boxes.length - 1; i >= 0; i--) {
            panelList.appendChild(buildPanelRow(i));
        }
    }

    function openPanel(e) {
        closePanel();
        panel = document.createElement("div");
        panel.className = "erpk-region-list";
        panel.style.position = "absolute";
        panel.style.zIndex = "20";
        panel.style.minWidth = "170px";
        panel.style.maxWidth = "280px";
        panel.style.maxHeight = Math.round(root.clientHeight * 0.6) + "px";
        panel.style.overflowY = "auto";
        panel.style.overflowX = "hidden";
        panel.style.scrollbarWidth = "thin";
        panel.style.scrollbarColor = "rgba(255, 255, 255, 0.25) transparent";
        panel.style.boxSizing = "border-box";
        panel.style.padding = "4px";
        panel.style.background = PANEL_BG;
        panel.style.border = "1px solid " + HAIRLINE;
        panel.style.borderRadius = "6px";
        panel.style.boxShadow = "0 4px 14px rgba(0, 0, 0, 0.45)";

        const header = document.createElement("div");
        header.textContent = "Regions · top = front";
        header.title = "Click a row to select · drag rows to reorder depth · "
            + "⧉ duplicates · ✕ deletes";
        header.style.font = "8px 'Segoe UI', sans-serif";
        header.style.color = "rgba(255, 255, 255, 0.45)";
        header.style.padding = "2px 6px 4px";
        header.style.whiteSpace = "nowrap";
        header.style.overflow = "hidden";
        header.style.textOverflow = "ellipsis";
        header.style.borderBottom = "1px solid " + HAIRLINE;
        header.style.marginBottom = "3px";
        panel.appendChild(header);

        panelList = document.createElement("div");
        panel.appendChild(panelList);
        renderPanelRows();

        panel.addEventListener("pointerdown", onPanelPointerDown);
        panel.addEventListener("contextmenu", onPanelContextMenu);

        // Append first so the measured size can clamp the position fully
        // inside the root.
        root.appendChild(panel);
        const pt = panelPoint(e);
        const maxX = Math.max(root.clientWidth - panel.offsetWidth - 4, 0);
        const maxY = Math.max(root.clientHeight - panel.offsetHeight - 4, 0);
        panel.style.left = Math.round(Math.min(Math.max(pt.x, 4), maxX)) + "px";
        panel.style.top = Math.round(Math.min(Math.max(pt.y, 4), maxY)) + "px";

        document.addEventListener("pointerdown", onDocPointerDown, true);
        document.addEventListener("keydown", onDocKeyDown, true);
    }

    // Suppresses both the browser and ComfyUI menus; a second right-click
    // closes the panel.
    function onContextMenu(e) {
        e.preventDefault();
        e.stopPropagation();
        if (panel) closePanel();
        else openPanel(e);
    }

    canvas.addEventListener("pointerdown", onPointerDown);
    canvas.addEventListener("pointermove", onPointerMove);
    canvas.addEventListener("pointerup", onPointerUp);
    canvas.addEventListener("pointercancel", onPointerUp);
    canvas.addEventListener("dblclick", onDblClick);
    canvas.addEventListener("keydown", onKeyDown);
    canvas.addEventListener("contextmenu", onContextMenu);
    helpBtn.addEventListener("pointerdown", onHelpPointerDown);
    inspector.addEventListener("pointerdown", onInspectorPointerDown);
    inspector.addEventListener("keydown", onInspectorKeyDown);
    descInput.addEventListener("input", onDescInput);
    kindSelect.addEventListener("change", onKindChange);
    textInput.addEventListener("input", onTextInput);
    clearBtn.addEventListener("click", onClearClick);
    backBtn.addEventListener("click", onSendBack);
    frontBtn.addEventListener("click", onBringForward);
    plugBtn.addEventListener("click", onPlugToggle);
    gridBtn.addEventListener("click", onGridToggle);
    gridSizeInput.addEventListener("input", onGridSizeInput);
    gridSizeInput.addEventListener("blur", onGridSizeBlur);
    gridSizeInput.addEventListener("keydown", onGridSizeKeyDown);
    gridColorInput.addEventListener("input", onGridColorInput);
    gridAlphaInput.addEventListener("input", onGridAlphaInput);
    gridAlphaInput.addEventListener("blur", onGridAlphaBlur);
    gridAlphaInput.addEventListener("keydown", onGridSizeKeyDown);
    snapBtn.addEventListener("click", onSnapToggle);

    const observer = new ResizeObserver(() => layout());
    observer.observe(stage);

    function setup() {
        hideRegionsWidget();
        hookDimensionWidget("width");
        hookDimensionWidget("height");
        restoreGridPrefs();
        syncDescSockets();
    }

    function destroy() {
        observer.disconnect();
        canvas.removeEventListener("pointerdown", onPointerDown);
        canvas.removeEventListener("pointermove", onPointerMove);
        canvas.removeEventListener("pointerup", onPointerUp);
        canvas.removeEventListener("pointercancel", onPointerUp);
        canvas.removeEventListener("dblclick", onDblClick);
        canvas.removeEventListener("keydown", onKeyDown);
        canvas.removeEventListener("contextmenu", onContextMenu);
        helpBtn.removeEventListener("pointerdown", onHelpPointerDown);
        inspector.removeEventListener("pointerdown", onInspectorPointerDown);
        inspector.removeEventListener("keydown", onInspectorKeyDown);
        descInput.removeEventListener("input", onDescInput);
        kindSelect.removeEventListener("change", onKindChange);
        textInput.removeEventListener("input", onTextInput);
        clearBtn.removeEventListener("click", onClearClick);
        backBtn.removeEventListener("click", onSendBack);
        frontBtn.removeEventListener("click", onBringForward);
        plugBtn.removeEventListener("click", onPlugToggle);
        gridBtn.removeEventListener("click", onGridToggle);
        gridSizeInput.removeEventListener("input", onGridSizeInput);
        gridSizeInput.removeEventListener("blur", onGridSizeBlur);
        gridSizeInput.removeEventListener("keydown", onGridSizeKeyDown);
        gridColorInput.removeEventListener("input", onGridColorInput);
        gridAlphaInput.removeEventListener("input", onGridAlphaInput);
        gridAlphaInput.removeEventListener("blur", onGridAlphaBlur);
        gridAlphaInput.removeEventListener("keydown", onGridSizeKeyDown);
        snapBtn.removeEventListener("click", onSnapToggle);
        closePanel();
        if (clearArm) clearTimeout(clearArm);
    }

    return { root, setup, loadFromWidget, layout, destroy };
}

app.registerExtension({
    name: "erpk.regionEditor",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData?.name !== NODE_ID) return;

        // The editor's height reaches the layout through the DOM widget's
        // getMinHeight/getMaxHeight (computeSize folds widget layout sizes in
        // by itself), so the node override only floors the width.
        const origComputeSize = nodeType.prototype.computeSize;
        nodeType.prototype.computeSize = function () {
            const size = origComputeSize?.apply(this, arguments) ?? [MIN_NODE_WIDTH, 0];
            return [Math.max(size[0], MIN_NODE_WIDTH), size[1]];
        };

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = onNodeCreated?.apply(this, arguments);

            const editor = createRegionEditor(this);
            this._erpkRegionEditor = editor;

            this.addDOMWidget("region_editor", "erpk_region_editor", editor.root, {
                serialize: false,
                hideOnZoom: false,
                // Pinning min == max keeps the canvas aspect-true at the node's
                // width and leaves the multiline scene field as the only widget
                // that grows when the node is stretched taller.
                getMinHeight: () => desiredEditorHeight(this),
                getMaxHeight: () => desiredEditorHeight(this),
            });

            const computed = this.computeSize();
            if (this.size[0] < computed[0]) this.size[0] = computed[0];
            if (this.size[1] < computed[1]) this.size[1] = computed[1];
            pinRootWidth(this);

            // Widgets (including regions_data) can finish materializing after
            // creation; defer the lookup-dependent setup until they exist.
            setTimeout(() => {
                editor.setup();
                editor.loadFromWidget();
                editor.layout();
            }, 50);

            return r;
        };

        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            const r = onConfigure?.apply(this, arguments);
            const editor = this._erpkRegionEditor;
            if (editor) {
                // Widget values from the workflow JSON land during configure;
                // re-read them once the restore has settled.
                setTimeout(() => {
                    editor.setup();
                    editor.loadFromWidget();
                    pinRootWidth(this);
                    editor.layout();
                }, 50);
            }
            return r;
        };

        const origOnResize = nodeType.prototype.onResize;
        nodeType.prototype.onResize = function (size) {
            const r = origOnResize?.apply(this, arguments);
            pinRootWidth(this);
            this._erpkRegionEditor?.layout();
            return r;
        };

        // Repaint when the reference image link is attached or removed.
        const origOnConnectionsChange = nodeType.prototype.onConnectionsChange;
        nodeType.prototype.onConnectionsChange = function () {
            const r = origOnConnectionsChange?.apply(this, arguments);
            this._erpkRegionEditor?.layout();
            return r;
        };

        const onRemoved = nodeType.prototype.onRemoved;
        nodeType.prototype.onRemoved = function () {
            this._erpkRegionEditor?.destroy();
            this._erpkRegionEditor = null;
            return onRemoved?.apply(this, arguments);
        };
    },
});
