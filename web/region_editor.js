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
// Twelfths subdivide both the rule-of-thirds guides and quarters cleanly.
const GRID_DIVS = 12;
// Horizontal padding the editor root carries inside the DOM widget wrapper.
const ROOT_PADDING_H = 8;
const STATUS_STRIP_H = 22;
const INSPECTOR_H = 26;
// Vertical chrome around the canvas inside the editor root: padding, canvas
// border, the inspector row, the status strip, and the flex gaps between them.
const EDITOR_CHROME_V = 66;

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

function clamp(v, lo, hi) {
    return Math.min(Math.max(v, lo), hi);
}

function round4(v) {
    return Math.round(v * 10000) / 10000;
}

function findWidget(node, name) {
    return node.widgets?.find((w) => w.name === name) ?? null;
}

function frameAspect(node) {
    const w = Number(findWidget(node, "width")?.value) || 1024;
    const h = Number(findWidget(node, "height")?.value) || 1024;
    return w > 0 && h > 0 ? w / h : 1;
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
        selected: -1,
        drag: null,      // {mode: "create"|"move"|"resize", ...}
        cssW: 0,
        cssH: 0,
        gridOn: false,
        snapOn: false,
    };

    // --- DOM scaffold -------------------------------------------------
    const root = document.createElement("div");
    root.className = "erpk-region-editor";
    root.style.position = "relative";
    root.style.display = "flex";
    root.style.flexDirection = "column";
    root.style.gap = "4px";
    root.style.padding = "4px";
    root.style.boxSizing = "border-box";
    root.style.width = "100%";
    root.style.height = "100%";
    root.style.minHeight = "160px";
    root.style.overflow = "hidden";

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
    status.style.padding = "0 8px";
    status.style.boxSizing = "border-box";
    status.style.background = PANEL_BG;
    status.style.border = "1px solid rgba(255, 255, 255, 0.08)";
    status.style.borderRadius = "3px";
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
    statusRight.style.flex = "0 0 auto";
    statusRight.style.fontVariantNumeric = "tabular-nums";
    function makeStripButton(label) {
        const btn = document.createElement("button");
        btn.type = "button";
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
    gridBtn.title = "Toggle the 12×12 grid";
    const snapBtn = makeStripButton("⌖");
    snapBtn.title = "Snap drawing, moving, and resizing to the grid";
    const clearBtn = makeStripButton("✕");
    clearBtn.title = "Clear all regions (click twice to confirm)";
    status.appendChild(statusLeft);
    status.appendChild(statusRight);
    status.appendChild(gridBtn);
    status.appendChild(snapBtn);
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

    const backBtn = makeStripButton("▼");
    backBtn.title = "Send back — one layer toward the background ( [ )";
    const frontBtn = makeStripButton("▲");
    frontBtn.title = "Bring forward — one layer toward the front ( ] )";

    inspector.appendChild(descInput);
    inspector.appendChild(kindSelect);
    inspector.appendChild(textInput);
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
        state.selected = -1;
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
        const isSelected = index === state.selected;

        ctx.fillStyle = color + (isSelected ? "2e" : "17");
        ctx.fillRect(x, y, w, h);
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

        // Numbered tape tag in the region's hue, description riding alongside.
        ctx.font = LABEL_FONT;
        const tag = String(index + 1);
        const tagW = Math.ceil(ctx.measureText(tag).width) + 8;
        ctx.fillStyle = color;
        ctx.fillRect(x, y, tagW, 15);
        ctx.fillStyle = INK_ON_TAPE;
        ctx.fillText(tag, x + 4, y + 11.5);
        if (box.desc) {
            const label = truncateLabel(box.desc, Math.max(w - tagW - 28, 12));
            const labelWidth = ctx.measureText(label).width;
            ctx.fillStyle = "rgba(8, 8, 10, 0.72)";
            ctx.fillRect(x + tagW, y, labelWidth + 10, 15);
            ctx.fillStyle = "rgba(255, 255, 255, 0.92)";
            ctx.fillText(label, x + tagW + 5, y + 11.5);
        }

        if (box.kind === "text") {
            const bx = x + w - 16;
            ctx.fillStyle = color;
            ctx.fillRect(bx, y + h - 16, 14, 14);
            ctx.fillStyle = INK_ON_TAPE;
            ctx.fillText("T", bx + 4, y + h - 5);
        }

        if (isSelected) {
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

    function snapCoord(v) {
        if (!(state.gridOn && state.snapOn)) return v;
        return clamp(Math.round(v * GRID_DIVS) / GRID_DIVS, 0, 1);
    }

    function snapPoint(p) {
        return { x: snapCoord(p.x), y: snapCoord(p.y) };
    }

    function drawGrid() {
        if (!state.gridOn) return;
        ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
        ctx.lineWidth = 1;
        for (let i = 1; i < GRID_DIVS; i++) {
            const f = i / GRID_DIVS;
            ctx.beginPath();
            ctx.moveTo(f * state.cssW, 0);
            ctx.lineTo(f * state.cssW, state.cssH);
            ctx.moveTo(0, f * state.cssH);
            ctx.lineTo(state.cssW, f * state.cssH);
            ctx.stroke();
        }
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
        ctx.fillText("Select to edit below · Delete removes", cx, cy + 44);
        ctx.textAlign = "left";
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
        const box = state.boxes[state.selected];
        if (box) {
            const sel = document.createElement("span");
            const name = box.kind === "text"
                ? (box.text || box.desc || "text")
                : (box.desc || "unnamed");
            sel.textContent = ` · #${state.selected + 1} ${name}`;
            sel.style.color = regionColor(state.selected);
            statusLeft.appendChild(sel);
        }
        const w = Number(findWidget(node, "width")?.value) || 1024;
        const h = Number(findWidget(node, "height")?.value) || 1024;
        statusRight.textContent = `${w}×${h} · ${ratioString(w, h)}`;
        clearBtn.style.opacity = count ? "1" : "0.45";
        clearBtn.style.cursor = count ? "pointer" : "default";
        if (!count) disarmClear();
        syncInspector();
    }

    function render() {
        if (!state.cssW || !state.cssH) return;
        const dpr = window.devicePixelRatio || 1;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.clearRect(0, 0, state.cssW, state.cssH);
        drawGrid();
        drawGuides();
        if (!state.boxes.length && !state.drag) drawEmptyHint();
        state.boxes.forEach((box, i) => drawBox(box, i));
        if (state.drag?.mode === "create") drawPending();
        renderStatus();
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
        if (state.selected < 0) return null;
        const box = state.boxes[state.selected];
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

    // Topmost box wins: later boxes draw above earlier ones.
    function hitBox(p) {
        for (let i = state.boxes.length - 1; i >= 0; i--) {
            const b = state.boxes[i];
            if (p.x >= b.x && p.x <= b.x + b.w && p.y >= b.y && p.y <= b.y + b.h) {
                return i;
            }
        }
        return -1;
    }

    function resizeAnchor(box, handleId) {
        if (handleId === "nw") return { x: box.x + box.w, y: box.y + box.h };
        if (handleId === "ne") return { x: box.x, y: box.y + box.h };
        if (handleId === "sw") return { x: box.x + box.w, y: box.y };
        return { x: box.x, y: box.y };
    }

    function updateCursor(e) {
        const handleId = hitHandle(pointerPx(e));
        if (handleId) {
            canvas.style.cursor =
                handleId === "nw" || handleId === "se" ? "nwse-resize" : "nesw-resize";
            return;
        }
        const hit = hitBox(pointerNorm(e));
        if (hit >= 0 && hit === state.selected) {
            canvas.style.cursor = "move";
        } else if (hit >= 0) {
            canvas.style.cursor = "pointer";
        } else {
            canvas.style.cursor = "crosshair";
        }
    }

    // --- Inspector flow ----------------------------------------------------
    // Repopulate only when the selected region object changes, so the render
    // loop never clobbers live typing or resets the cursor.
    let inspected = null;

    function syncInspector() {
        const box = state.boxes[state.selected] ?? null;
        if (box === inspected) {
            textInput.disabled = !box || box.kind !== "text";
            return;
        }
        inspected = box;
        descInput.value = box ? box.desc : "";
        kindSelect.value = box ? box.kind : "object";
        textInput.value = box ? box.text : "";
        const off = !box;
        descInput.disabled = off;
        kindSelect.disabled = off;
        textInput.disabled = off || box.kind !== "text";
        backBtn.disabled = off;
        frontBtn.disabled = off;
        const dim = off ? "0.45" : "1";
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
        if (state.selected < 0) return;
        state.selected = moveRegion(state.selected, delta);
        render();
    }

    // --- Event handlers ----------------------------------------------------
    function onPointerDown(e) {
        if (e.button !== 0) return;
        e.stopPropagation();
        canvas.focus();
        canvas.setPointerCapture(e.pointerId);

        const p = pointerNorm(e);
        const handleId = hitHandle(pointerPx(e));
        if (handleId) {
            const box = state.boxes[state.selected];
            state.drag = { mode: "resize", anchor: resizeAnchor(box, handleId) };
        } else {
            const hit = hitBox(p);
            if (hit >= 0) {
                state.selected = hit;
                const box = state.boxes[hit];
                state.drag = { mode: "move", grabDX: p.x - box.x, grabDY: p.y - box.y };
            } else {
                state.selected = -1;
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
        } else if (d.mode === "move") {
            const box = state.boxes[state.selected];
            if (!box) return;
            box.x = clamp(snapCoord(p.x - d.grabDX), 0, 1 - box.w);
            box.y = clamp(snapCoord(p.y - d.grabDY), 0, 1 - box.h);
        } else if (d.mode === "resize") {
            const box = state.boxes[state.selected];
            if (!box) return;
            Object.assign(box, rectFrom(d.anchor, snapPoint(p)));
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
                state.boxes.push({ ...rect, kind: "object", desc: "", text: "" });
                state.selected = state.boxes.length - 1;
                syncWidget();
            }
        } else {
            const box = state.boxes[state.selected];
            if (box) {
                enforceMinSize(box);
                syncWidget();
            }
        }
        render();
    }

    function onDblClick(e) {
        e.stopPropagation();
        const hit = hitBox(pointerNorm(e));
        if (hit < 0) return;
        state.selected = hit;
        render();
        descInput.focus();
        descInput.select();
    }

    function onKeyDown(e) {
        if (
            (e.key === "Delete" || e.key === "Backspace")
            && state.selected >= 0
        ) {
            e.preventDefault();
            e.stopPropagation();
            state.boxes.splice(state.selected, 1);
            state.selected = -1;
            syncWidget();
            render();
            return;
        }
        if ((e.key === "[" || e.key === "]") && state.selected >= 0) {
            e.preventDefault();
            e.stopPropagation();
            state.selected = moveRegion(state.selected, e.key === "]" ? 1 : -1);
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
        const box = state.boxes[state.selected];
        if (!box) return;
        box.desc = descInput.value;
        syncWidget();
        render();
    }

    function onKindChange() {
        const box = state.boxes[state.selected];
        if (!box) return;
        box.kind = kindSelect.value === "text" ? "text" : "object";
        textInput.disabled = box.kind !== "text";
        syncWidget();
        render();
    }

    function onTextInput() {
        const box = state.boxes[state.selected];
        if (!box) return;
        box.text = textInput.value;
        syncWidget();
        render();
    }

    // Grid/snap are editor preferences, persisted through node.properties so
    // they travel with the workflow without touching the widget schema.
    function persistGridPrefs() {
        if (!node.properties) node.properties = {};
        node.properties.erpk_region_grid = { grid: state.gridOn, snap: state.snapOn };
    }

    function restoreGridPrefs() {
        const saved = node.properties?.erpk_region_grid;
        if (saved && typeof saved === "object") {
            state.gridOn = !!saved.grid;
            state.snapOn = !!saved.snap;
        }
        syncToolButtons();
    }

    function syncToolButtons() {
        const on = "rgba(255, 255, 255, 0.92)";
        const off = "rgba(255, 255, 255, 0.65)";
        const onBorder = "rgba(255, 255, 255, 0.45)";
        const offBorder = "rgba(255, 255, 255, 0.14)";
        gridBtn.style.color = state.gridOn ? on : off;
        gridBtn.style.borderColor = state.gridOn ? onBorder : offBorder;
        const snapActive = state.gridOn && state.snapOn;
        snapBtn.style.opacity = state.gridOn ? "1" : "0.45";
        snapBtn.style.cursor = state.gridOn ? "pointer" : "default";
        snapBtn.style.color = snapActive ? on : off;
        snapBtn.style.borderColor = snapActive ? onBorder : offBorder;
    }

    function onGridToggle() {
        state.gridOn = !state.gridOn;
        persistGridPrefs();
        syncToolButtons();
        render();
    }

    function onSnapToggle() {
        if (!state.gridOn) return;
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
        clearBtn.textContent = "✕";
        clearBtn.style.color = "rgba(255, 255, 255, 0.65)";
        clearBtn.style.borderColor = "rgba(255, 255, 255, 0.14)";
    }

    function onClearClick() {
        if (!state.boxes.length) return;
        if (clearArm === null) {
            clearBtn.textContent = "Confirm?";
            clearBtn.style.color = "#f9a826";
            clearBtn.style.borderColor = "#f9a826";
            clearArm = setTimeout(disarmClear, 2500);
            return;
        }
        disarmClear();
        state.boxes = [];
        state.selected = -1;
        syncWidget();
        render();
    }

    function onSendBack() {
        moveSelectedRegion(-1);
    }

    function onBringForward() {
        moveSelectedRegion(1);
    }

    canvas.addEventListener("pointerdown", onPointerDown);
    canvas.addEventListener("pointermove", onPointerMove);
    canvas.addEventListener("pointerup", onPointerUp);
    canvas.addEventListener("pointercancel", onPointerUp);
    canvas.addEventListener("dblclick", onDblClick);
    canvas.addEventListener("keydown", onKeyDown);
    inspector.addEventListener("pointerdown", onInspectorPointerDown);
    inspector.addEventListener("keydown", onInspectorKeyDown);
    descInput.addEventListener("input", onDescInput);
    kindSelect.addEventListener("change", onKindChange);
    textInput.addEventListener("input", onTextInput);
    clearBtn.addEventListener("click", onClearClick);
    backBtn.addEventListener("click", onSendBack);
    frontBtn.addEventListener("click", onBringForward);
    gridBtn.addEventListener("click", onGridToggle);
    snapBtn.addEventListener("click", onSnapToggle);

    const observer = new ResizeObserver(() => layout());
    observer.observe(stage);

    function setup() {
        hideRegionsWidget();
        hookDimensionWidget("width");
        hookDimensionWidget("height");
        restoreGridPrefs();
    }

    function destroy() {
        observer.disconnect();
        canvas.removeEventListener("pointerdown", onPointerDown);
        canvas.removeEventListener("pointermove", onPointerMove);
        canvas.removeEventListener("pointerup", onPointerUp);
        canvas.removeEventListener("pointercancel", onPointerUp);
        canvas.removeEventListener("dblclick", onDblClick);
        canvas.removeEventListener("keydown", onKeyDown);
        inspector.removeEventListener("pointerdown", onInspectorPointerDown);
        inspector.removeEventListener("keydown", onInspectorKeyDown);
        descInput.removeEventListener("input", onDescInput);
        kindSelect.removeEventListener("change", onKindChange);
        textInput.removeEventListener("input", onTextInput);
        clearBtn.removeEventListener("click", onClearClick);
        backBtn.removeEventListener("click", onSendBack);
        frontBtn.removeEventListener("click", onBringForward);
        gridBtn.removeEventListener("click", onGridToggle);
        snapBtn.removeEventListener("click", onSnapToggle);
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

        const onRemoved = nodeType.prototype.onRemoved;
        nodeType.prototype.onRemoved = function () {
            this._erpkRegionEditor?.destroy();
            this._erpkRegionEditor = null;
            return onRemoved?.apply(this, arguments);
        };
    },
});
