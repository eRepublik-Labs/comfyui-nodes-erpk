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
// Matches DESC_INPUT_COUNT / REF_INPUT_COUNT on the Python side.
const REGION_DESC_INPUTS = 10;
const REGION_REF_INPUTS = 10;
// Upper bound the vision scan asks the engine for; mirrors the route default.
const SCAN_MAX_OBJECTS = 20;
const SCAN_MAX_EDGE_PX = 1536;

// Grid cell size is expressed in frame pixels, so the grid quantizes to the
// generated image's own pixel space (64 aligns with latent blocks).
const GRID_MIN_CELL_PX = 8;
const GRID_MAX_CELL_PX = 1024;
const GRID_DEFAULT_CELL_PX = 64;
const GRID_DEFAULT_COLOR = "#26262e";
// Active/toggled-on state for strip and inspector controls.
const ACTIVE_GREEN = "#52c97d";
const ACTIVE_GREEN_BORDER = "rgba(82, 201, 125, 0.55)";
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
.erpk-btn-active:hover:not(:disabled) {
    color: #6fe39a !important;
    border-color: #6fe39a !important;
}
@keyframes erpk-spin { to { transform: rotate(360deg); } }
.erpk-spinner {
    display: inline-block;
    width: 13px;
    height: 13px;
    border-radius: 50%;
    border: 2.5px solid rgba(255, 255, 255, 0.2);
    border-top-color: #fff;
    animation: erpk-spin 0.7s linear infinite;
}
@keyframes erpk-pulse { 50% { opacity: 0.45; } }
.erpk-scan-text {
    color: ${ACTIVE_GREEN};
    animation: erpk-pulse 1.2s ease-in-out infinite;
}
.erpk-stage-btn { opacity: 0.6; }
.erpk-stage-btn:hover:not(:disabled),
.erpk-stage-btn[data-busy="1"],
.erpk-stage-btn.erpk-btn-active {
    opacity: 1 !important;
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

// Visibility toggles render a real eye: open when shown, struck when hidden.
const EYE_SVG =
    '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" '
    + 'stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
    + 'stroke-linejoin="round" style="display:block">'
    + '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/>'
    + '<circle cx="12" cy="12" r="3"/></svg>';
const EYE_OFF_SVG =
    '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" '
    + 'stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
    + 'stroke-linejoin="round" style="display:block">'
    + '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/>'
    + '<circle cx="12" cy="12" r="3"/>'
    + '<line x1="4" y1="20" x2="20" y2="4"/></svg>';

function setEyeIcon(btn, hidden) {
    btn.innerHTML = hidden ? EYE_OFF_SVG : EYE_SVG;
}

// Regions cycle through gaffer-tape hues so each keeps a stable identity on
// the stage; kind is marked by the T badge and rendered text, not by color.
const TAPE_COLORS = ["#4cc9f0", "#f9a826", "#f15bb5", "#9ef01a", "#9b5de5", "#ff6d5a"];

function regionColor(index) {
    return TAPE_COLORS[index % TAPE_COLORS.length];
}

// Deterministic small hash so a class label always maps to the same hue.
function hashString(str) {
    let h = 0;
    for (let i = 0; i < str.length; i++) {
        h = (h * 31 + str.charCodeAt(i)) | 0;
    }
    return h;
}

// Scanned regions carry a class label in box.group; same-label regions share a
// hue so the object layer reads as classes. Hand-drawn regions keep their
// index-cycled identity color.
function colorForRegion(box, index) {
    if (box.group) {
        return TAPE_COLORS[Math.abs(hashString(box.group)) % TAPE_COLORS.length];
    }
    return regionColor(index);
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

// Glyph ink on a tape chip: the chip's own hue scaled toward black reads as
// a shade of the region color instead of a foreign white or black.
function darkenHex(hex, factor) {
    const r = Math.round(parseInt(hex.slice(1, 3), 16) * factor);
    const g = Math.round(parseInt(hex.slice(3, 5), 16) * factor);
    const b = Math.round(parseInt(hex.slice(5, 7), 16) * factor);
    return `rgb(${r}, ${g}, ${b})`;
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
    // While expanded the root is a viewport overlay, not a node-width box.
    if (!root || root._erpkExpanded) return;
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
        const region = {
            x, y, w, h,
            kind: entry.kind === "text" ? "text" : "object",
            desc: typeof entry.desc === "string" ? entry.desc : "",
            text: typeof entry.text === "string" ? entry.text : "",
        };
        // Scan-produced optionals: a box-relative base64 PNG mask, a class
        // label, and the origin box. Absent for hand-drawn regions, which stay
        // backward compatible.
        if (typeof entry.mask === "string" && entry.mask) region.mask = entry.mask;
        if (typeof entry.group === "string" && entry.group) region.group = entry.group;
        // View-only flag: a hidden region skips drawing and hit-testing but
        // still feeds the prompt, bbox, and mask outputs.
        if (entry.hidden === true) region.hidden = true;
        if (entry.src && typeof entry.src === "object") {
            const sn = [entry.src.x, entry.src.y, entry.src.w, entry.src.h]
                .map((v) => Number(v ?? NaN));
            if (sn.every(Number.isFinite)) {
                const sx = clamp(sn[0], 0, 1);
                const sy = clamp(sn[1], 0, 1);
                const sw = clamp(sn[2], 0, 1 - sx);
                const sh = clamp(sn[3], 0, 1 - sy);
                if (sw > 0.005 && sh > 0.005) {
                    region.src = { x: sx, y: sy, w: sw, h: sh };
                }
            }
        }
        // Regions scanned before origins existed: an unmoved region's current
        // geometry IS its origin, so backfill and the move preview lights up.
        if (region.mask && !region.src) {
            region.src = { x, y, w, h };
        }
        regions.push(region);
    }
    return regions;
}

function serializeRegions(boxes) {
    return JSON.stringify(boxes.map((b) => {
        const out = {
            x: round4(b.x),
            y: round4(b.y),
            w: round4(b.w),
            h: round4(b.h),
            kind: b.kind,
            desc: b.desc,
            text: b.text,
        };
        // Only scanned regions carry these; spreading them only when truthy
        // keeps hand-drawn regions' serialized payload compact.
        if (b.mask) out.mask = b.mask;
        if (b.group) out.group = b.group;
        if (b.hidden) out.hidden = true;
        if (b.src) {
            out.src = { x: round4(b.src.x), y: round4(b.src.y),
                        w: round4(b.src.w), h: round4(b.src.h) };
        }
        return out;
    }));
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
        hoverIndex: -1,  // region under the cursor (mask-aware); its mask glows
        cssW: 0,
        cssH: 0,
        hideBoxes: false,      // view-only: skip drawing and hit-testing boxes
        gridShow: false,
        gridCellPx: GRID_DEFAULT_CELL_PX,
        gridColor: GRID_DEFAULT_COLOR,
        gridAlpha: 1,
        snapOn: false,
        scanning: false,      // a vision scan request is in flight
        showMasks: false,      // overlay the scan's segmentation masks
        scanError: null,       // last scan failure, surfaced in the status strip
        scanAbort: null,       // AbortController for the in-flight scan
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
    // Positioned so the floating scan button anchors to the stage corner.
    stage.style.position = "relative";
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

    // Square buttons floating over the stage corners share the strip buttons'
    // visual language; the canvas backdrop needs the slight fill for contrast.
    function floatOnStage(btn, side) {
        btn.classList.add("erpk-stage-btn");
        btn.style.position = "absolute";
        btn.style[side] = "6px";
        btn.style.top = "6px";
        btn.style.zIndex = "10";
        btn.style.width = "24px";
        btn.style.height = "24px";
        btn.style.padding = "0";
        btn.style.display = "flex";
        btn.style.alignItems = "center";
        btn.style.justifyContent = "center";
        btn.style.fontSize = "13px";
        btn.style.color = "rgba(255, 255, 255, 0.9)";
        btn.style.background = "rgba(15, 15, 15, 0.8)";
        btn.style.border = "1px solid rgba(255, 255, 255, 0.3)";
        btn.style.borderRadius = "5px";
        stage.appendChild(btn);
    }

    const gridBtn = makeStripButton("⊞");
    gridBtn.dataset.tip = "Show grid";
    const gridSizeInput = document.createElement("input");
    gridSizeInput.type = "number";
    gridSizeInput.min = String(GRID_MIN_CELL_PX);
    gridSizeInput.max = String(GRID_MAX_CELL_PX);
    gridSizeInput.dataset.tip = "Grid cell size in frame pixels (8–1024)";
    styleInput(gridSizeInput);
    gridSizeInput.style.width = "48px";
    gridSizeInput.style.flex = "0 0 auto";
    gridSizeInput.style.padding = "1px 4px";
    gridSizeInput.style.fontSize = "10px";
    gridSizeInput.style.display = "none";
    const gridColorInput = document.createElement("input");
    gridColorInput.type = "color";
    gridColorInput.value = GRID_DEFAULT_COLOR;
    gridColorInput.dataset.tip = "Grid color";
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
    gridAlphaInput.dataset.tip = "Grid opacity in percent (5–100)";
    styleInput(gridAlphaInput);
    gridAlphaInput.style.width = "40px";
    gridAlphaInput.style.flex = "0 0 auto";
    gridAlphaInput.style.padding = "1px 4px";
    gridAlphaInput.style.fontSize = "10px";
    gridAlphaInput.style.display = "none";
    const snapBtn = makeStripButton("⌖");
    snapBtn.dataset.tip = "Snap drawing, moving, and resizing to the grid";
    const helpBtn = makeStripButton("?");
    helpBtn.dataset.tip = "Keyboard and mouse shortcuts";
    const gearBtn = makeStripButton("⚙");
    gearBtn.dataset.tip = "Scan options";
    const fsBtn = makeStripButton("⤢");
    fsBtn.dataset.tip = "Expand the editor to fill the window (F · Esc to exit)";
    floatOnStage(fsBtn, "right");
    const matchBtn = makeStripButton("⚠ match");
    matchBtn.style.font = "bold 9px 'Segoe UI', sans-serif";
    matchBtn.style.color = "rgba(249, 168, 38, 0.85)";
    matchBtn.style.borderColor = "rgba(249, 168, 38, 0.45)";
    matchBtn.style.display = "none";
    // Toggles the segmentation-mask overlay; enabled only when a region
    // actually carries a scanned mask.
    const maskBtn = makeStripButton("◐");
    maskBtn.dataset.tip = "Show segmentation masks";
    // Global overlay visibility, the strip twin of the H shortcut.
    const hideBtn = makeStripButton("");
    setEyeIcon(hideBtn, false);
    hideBtn.dataset.tip = "Hide all region overlays (H)";
    // Scans the connected image for objects. Floats in the stage's upper-left
    // rather than the strip, and only shows when an image is connected.
    const scanBtn = makeStripButton("✦");
    scanBtn.dataset.tip = "Scan the connected image for objects";
    floatOnStage(scanBtn, "left");
    scanBtn.style.display = "none";
    const clearBtn = makeStripButton("Clear all");
    clearBtn.classList.add("erpk-btn-danger");
    clearBtn.dataset.tip = "Remove every region (click twice to confirm)";
    clearBtn.style.font = "bold 9px 'Segoe UI', sans-serif";
    // The font override shrinks the box below its 12px siblings; pin it to
    // their rendered height (12px line + 1px padding + 1px border per side).
    clearBtn.style.height = "16px";
    clearBtn.style.boxSizing = "border-box";
    clearBtn.style.color = DANGER_RED_DIM;
    clearBtn.style.borderColor = DANGER_RED_BORDER;
    status.appendChild(statusLeft);
    status.appendChild(statusRight);
    status.appendChild(matchBtn);
    status.appendChild(maskBtn);
    status.appendChild(hideBtn);
    status.appendChild(gridBtn);
    status.appendChild(gridSizeInput);
    status.appendChild(gridColorInput);
    status.appendChild(gridAlphaInput);
    status.appendChild(snapBtn);
    status.appendChild(helpBtn);
    status.appendChild(gearBtn);
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
    descInput.dataset.tip = "Description of the selected region";
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
    kindSelect.dataset.tip = "Region kind: an object in the scene, or literal text to render";
    styleInput(kindSelect);
    kindSelect.style.width = "";
    kindSelect.style.flex = "0 0 auto";

    const textInput = document.createElement("input");
    textInput.type = "text";
    textInput.placeholder = "text to render";
    textInput.dataset.tip = "Literal text the model should render inside this region";
    styleInput(textInput);
    textInput.style.width = "";
    textInput.style.flex = "1 1 0";
    textInput.style.minWidth = "0";

    const plugBtn = makeStripButton("⌁");
    plugBtn.dataset.tip = "Expose this region's description as an input";
    const refBtn = makeStripButton("▣");
    refBtn.dataset.tip = "Attach a reference image input to this region";
    const backBtn = makeStripButton("▼");
    backBtn.dataset.tip = "Send back — one layer toward the background ( [ )";
    const frontBtn = makeStripButton("▲");
    frontBtn.dataset.tip = "Bring forward — one layer toward the front ( ] )";

    inspector.appendChild(descInput);
    inspector.appendChild(kindSelect);
    inspector.appendChild(textInput);
    inspector.appendChild(plugBtn);
    inspector.appendChild(refBtn);
    inspector.appendChild(backBtn);
    inspector.appendChild(frontBtn);
    root.insertBefore(inspector, status);

    // --- Widget plumbing ----------------------------------------------
    // Undo snapshots the serialized regions string inside syncWidget — the
    // single write path every mutation funnels through — so no gesture can
    // escape history. Pushes within the coalesce window merge into one step
    // (typing, arrow nudges); restores must not record themselves.
    const UNDO_LIMIT = 50;
    const UNDO_COALESCE_MS = 800;
    const undoStack = [];
    const redoStack = [];
    let undoLastPush = 0;
    let undoRestoring = false;

    function syncWidget() {
        const widget = findWidget(node, "regions_data");
        if (widget) {
            const next = serializeRegions(state.boxes);
            const prev = widget.value;
            if (!undoRestoring && typeof prev === "string" && prev !== next) {
                const now = performance.now();
                if (now - undoLastPush > UNDO_COALESCE_MS) {
                    undoStack.push(prev);
                    if (undoStack.length > UNDO_LIMIT) undoStack.shift();
                }
                undoLastPush = now;
                redoStack.length = 0;
            }
            widget.value = next;
        }
        node.setDirtyCanvas?.(true, true);
    }

    function restoreSnapshot(snapshot) {
        state.boxes = parseRegions(snapshot);
        clearSelection();
        undoRestoring = true;
        syncWidget();
        undoRestoring = false;
        render();
    }

    function undoRegions() {
        const widget = findWidget(node, "regions_data");
        if (!widget) return;
        const current = widget.value;
        while (undoStack.length && undoStack[undoStack.length - 1] === current) {
            undoStack.pop();
        }
        if (!undoStack.length) return;
        redoStack.push(current);
        restoreSnapshot(undoStack.pop());
    }

    function redoRegions() {
        const widget = findWidget(node, "regions_data");
        if (!widget || !redoStack.length) return;
        undoStack.push(widget.value);
        restoreSnapshot(redoStack.pop());
    }

    function loadFromWidget() {
        const widget = findWidget(node, "regions_data");
        state.boxes = parseRegions(widget?.value ?? "[]");
        // A (re)loaded workflow is a fresh document; stale history would
        // restore another graph's regions.
        undoStack.length = 0;
        redoStack.length = 0;
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
        // Fit the frame aspect inside the stage on whichever axis binds: in the
        // node the height is pinned to width/aspect so width wins, and in the
        // fullscreen overlay either axis can bind. The stage centers the result,
        // letterboxing the spare axis.
        const aspect = frameAspect(node);
        const cw = Math.min(availW, availH * aspect);
        const ch = cw / aspect;
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

    // Greedy word wrap; once rows run out the remainder ellipsizes onto the
    // last one. Lines a single word can't shrink to also ellipsize.
    function wrapLabel(text, maxWidth, maxRows) {
        const words = text.split(/\s+/).filter(Boolean);
        const lines = [];
        let line = "";
        for (let i = 0; i < words.length; i++) {
            const candidate = line ? line + " " + words[i] : words[i];
            if (!line || ctx.measureText(candidate).width <= maxWidth) {
                line = candidate;
            } else if (lines.length < maxRows - 1) {
                lines.push(truncateLabel(line, maxWidth));
                line = words[i];
            } else {
                lines.push(truncateLabel(
                    candidate + " " + words.slice(i + 1).join(" "), maxWidth));
                return lines;
            }
        }
        lines.push(truncateLabel(line, maxWidth));
        return lines;
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
        if (box.hidden) return;
        const x = box.x * state.cssW;
        const y = box.y * state.cssH;
        const w = box.w * state.cssW;
        const h = box.h * state.cssH;
        const color = colorForRegion(box, index);
        const isSelected = state.selection.has(box);

        // A moved scanned region previews its relocation: the masked cut-out
        // from the origin follows the box; the origin shows an erase-preview
        // (the silhouette dimmed and hatched — "this gets removed"), and an
        // arrow ties origin to destination. Clicking the ghost snaps back.
        if (box.mask && regionMoved(box)) {
            const cutout = cutoutFor(box);
            if (cutout) ctx.drawImage(cutout, x, y, w, h);
            const gx = box.src.x * state.cssW;
            const gy = box.src.y * state.cssH;
            const gw = box.src.w * state.cssW;
            const gh = box.src.h * state.cssH;
            const ghost = ghostCheckerFor(box, gw, gh);
            if (ghost) ctx.drawImage(ghost, gx, gy, gw, gh);
            ctx.save();
            ctx.setLineDash([4, 4]);
            ctx.strokeStyle = color + "66";
            ctx.lineWidth = 1;
            ctx.strokeRect(gx, gy, gw, gh);
            ctx.restore();
            drawMoveArrow(box, color);
        }

        ctx.fillStyle = color + (isSelected ? "2e" : "17");
        ctx.fillRect(x, y, w, h);

        // Diagonal hatching marks regions whose description is wired from a
        // desc_N input - the texture itself says "externally driven".
        if (descWiredFor(box)) {
            ctx.save();
            ctx.beginPath();
            ctx.rect(x, y, w, h);
            ctx.clip();
            ctx.strokeStyle = color + (isSelected ? "2c" : "18");
            ctx.lineWidth = 2;
            ctx.beginPath();
            for (let d = -h; d < w; d += 12) {
                ctx.moveTo(x + d, y + h);
                ctx.lineTo(x + d + h, y);
            }
            ctx.stroke();
            ctx.restore();
        }

        ctx.strokeStyle = color;
        ctx.lineWidth = isSelected || index === state.hoverIndex ? 2 : 1.5;
        ctx.strokeRect(x, y, w, h);

        // The scanned segmentation mask overlays the region in its own hue. The
        // mask is box-relative, so it maps 1:1 onto the box rect; multiplying
        // the region color through the probability map keeps the mask's shape.
        // Hovering a region glows its mask even when the overlay is off.
        const isHovered = index === state.hoverIndex;
        if ((state.showMasks || isHovered) && box.mask) {
            let maskImg = box._erpkMaskImg;
            if (!maskImg) {
                maskImg = new Image();
                maskImg.src = "data:image/png;base64," + box.mask;
                box._erpkMaskImg = maskImg;
            }
            if (maskImg.complete && maskImg.naturalWidth) {
                ctx.save();
                ctx.beginPath();
                ctx.rect(x, y, w, h);
                ctx.clip();
                ctx.globalAlpha = isHovered ? 0.6 : 0.4;
                ctx.fillStyle = color;
                ctx.fillRect(x, y, w, h);
                ctx.globalCompositeOperation = "multiply";
                ctx.drawImage(maskImg, x, y, w, h);
                ctx.restore();
            } else {
                maskImg.addEventListener("load", () => render(), { once: true });
            }
        }

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
        const ink = darkenHex(color, 0.25);
        ctx.font = "bold 9px 'Segoe UI', sans-serif";
        const tagW = Math.ceil(ctx.measureText(tag).width) + 7;
        ctx.fillStyle = color;
        ctx.fillRect(x, y, tagW, 13);
        ctx.fillStyle = ink;
        ctx.fillText(tag, x + 3.5, y + 9.5);
        let labelX = x + tagW;
        if (descWiredFor(box)) {
            const plugW = Math.ceil(ctx.measureText("⌁").width) + 7;
            ctx.fillStyle = color;
            ctx.fillRect(labelX + 1, y, plugW, 13);
            ctx.fillStyle = ink;
            ctx.fillText("⌁", labelX + 4.5, y + 9.5);
            labelX += plugW + 1;
        }
        if (refWiredFor(box)) {
            const chipW = Math.ceil(ctx.measureText("▣").width) + 7;
            ctx.fillStyle = color;
            ctx.fillRect(labelX + 1, y, chipW, 13);
            ctx.fillStyle = ink;
            ctx.fillText("▣", labelX + 4.5, y + 9.5);
            labelX += chipW + 1;
        }
        // The tag carries only the short layer name; the full prompt lives in
        // the hover tooltip and the right-click detail view.
        const tagText = box.group || box.desc;
        if (tagText) {
            ctx.font = LABEL_FONT;
            // The label wraps inside the region: rows break at the box's
            // right edge and ellipsize only when its height runs out of
            // 13px bands.
            const labelMax = Math.max(w - (labelX - x) - 6, 12);
            const maxRows = Math.max(1, Math.floor(h / 13));
            wrapLabel(tagText, labelMax, maxRows).forEach((line, row) => {
                const lineWidth = ctx.measureText(line).width;
                ctx.fillStyle = "rgba(8, 8, 10, 0.72)";
                ctx.fillRect(labelX, y + row * 13, lineWidth + 10, 13);
                ctx.fillStyle = "rgba(255, 255, 255, 0.92)";
                ctx.fillText(line, labelX + 5, y + row * 13 + 10);
            });
        }

        if (box.kind === "text") {
            ctx.font = LABEL_FONT;
            const bx = x + w - 16;
            ctx.fillStyle = color;
            ctx.fillRect(bx, y + h - 16, 14, 14);
            ctx.fillStyle = INK_ON_TAPE;
            ctx.fillText("T", bx + 4, y + h - 5);
        }

        // Attached reference preview in the bottom-left corner; squashed to a
        // square thumbnail (distortion is acceptable for a glanceable cue).
        if (refWiredFor(box)) {
            const thumb = upstreamImage(`ref_${index + 1}`);
            if (thumb && thumb.complete && thumb.naturalWidth) {
                const ts = clamp(Math.min(w, h) * 0.3, 14, 30);
                ctx.drawImage(thumb, x + 3, y + h - ts - 3, ts, ts);
                ctx.strokeStyle = color;
                ctx.lineWidth = 1;
                ctx.strokeRect(x + 3, y + h - ts - 3, ts, ts);
            } else if (thumb) {
                thumb.addEventListener("load", () => render(), { once: true });
            }
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

    // LoadImage and executed preview nodes expose their image client-side via
    // node.imgs; follow the link on the named input to its origin node.
    function upstreamImage(inputName) {
        const input = node.inputs?.find((i) => i.name === inputName);
        if (!input || input.link == null) return null;
        const link = node.graph?.links?.[input.link];
        const origin = link ? node.graph.getNodeById(link.origin_id) : null;
        return origin?.imgs?.[0] ?? null;
    }

    // Draws the upstream image stretched to the frame; a distorted reference
    // is the cue that width/height do not match the source image.
    function drawReference() {
        const img = upstreamImage("image");
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

    // Frame dimensions matching an image's aspect, scaled into the widget
    // range and snapped to the widgets' step of 8.
    function fitFrameToImage(iw, ih) {
        const down = Math.min(8192 / iw, 8192 / ih, 1);
        const up = Math.max(64 / (iw * down), 64 / (ih * down), 1);
        const w = Math.round((iw * down * up) / 8) * 8;
        const h = Math.round((ih * down * up) / 8) * 8;
        return { w: clamp(w, 64, 8192), h: clamp(h, 64, 8192) };
    }

    function renderStatus() {
        statusLeft.textContent = "";
        const count = state.boxes.length;
        const countSpan = document.createElement("span");
        if (state.scanning) {
            countSpan.textContent = "Scanning image for objects…";
            countSpan.classList.add("erpk-scan-text");
        } else {
            countSpan.textContent = count === 0
                ? "No regions yet"
                : `${count} region${count === 1 ? "" : "s"}`;
            countSpan.style.color = count === 0
                ? "rgba(255, 255, 255, 0.4)"
                : "rgba(255, 255, 255, 0.65)";
        }
        statusLeft.appendChild(countSpan);
        const index = primaryIndex();
        const box = index >= 0 ? state.boxes[index] : null;
        if (box) {
            const sel = document.createElement("span");
            const name = box.kind === "text"
                ? (box.text || box.group || box.desc || "text")
                : (box.group || box.desc || "unnamed");
            sel.textContent = ` · #${index + 1} ${name}`;
            sel.style.color = colorForRegion(box, index);
            statusLeft.appendChild(sel);
        }
        // A scan failure lives in state so it survives the rebuild-on-render;
        // it clears on the next scan attempt.
        if (state.scanError) {
            const err = document.createElement("span");
            err.textContent = ` · ${state.scanError}`;
            err.style.color = DANGER_RED;
            statusLeft.appendChild(err);
        }
        const w = Number(findWidget(node, "width")?.value) || 1024;
        const h = Number(findWidget(node, "height")?.value) || 1024;
        statusRight.textContent = `${w}×${h} · ${ratioString(w, h)}`;
        // An edit output follows the source image's canvas, so a frame whose
        // aspect differs from the connected reference composes for a shape
        // that will not exist; the chip offers a one-click match.
        const refImg = upstreamImage("image");
        let matchDims = null;
        if (refImg?.naturalWidth && refImg?.naturalHeight) {
            const imgAspect = refImg.naturalWidth / refImg.naturalHeight;
            if (Math.abs(imgAspect / (w / h) - 1) > 0.01) {
                matchDims = fitFrameToImage(refImg.naturalWidth, refImg.naturalHeight);
            }
        }
        matchBtn.style.display = matchDims ? "" : "none";
        if (matchDims) {
            matchBtn._erpkDims = matchDims;
            matchBtn.dataset.tip = `Frame ${w}×${h} doesn't match the `
                + `connected image ${refImg.naturalWidth}×${refImg.naturalHeight}`
                + ` — click to set ${matchDims.w}×${matchDims.h}`;
        }
        // The scan button only shows once a loaded image is connected, and
        // swaps to a spinner glyph while a scan is in flight.
        const scanReady = !!(refImg?.naturalWidth && refImg?.naturalHeight);
        scanBtn.style.display = scanReady ? "" : "none";
        scanBtn.disabled = state.scanning || !scanReady;
        // Swap content only on state edges: render() runs per frame, and
        // recreating the spinner each pass would restart its animation.
        const busy = scanBtn.dataset.busy === "1";
        if (state.scanning && !busy) {
            scanBtn.dataset.busy = "1";
            scanBtn.textContent = "";
            const spin = document.createElement("span");
            spin.className = "erpk-spinner";
            scanBtn.appendChild(spin);
        } else if (!state.scanning && busy) {
            delete scanBtn.dataset.busy;
            scanBtn.textContent = "✦";
        }
        scanBtn.style.cursor = state.scanning ? "default" : "pointer";
        // The mask toggle is enabled only when a region carries a scanned mask.
        const hasMask = state.boxes.some((b) => b.mask);
        const masksOn = hasMask && state.showMasks;
        maskBtn.disabled = !hasMask;
        maskBtn.style.opacity = hasMask ? "1" : "0.45";
        maskBtn.style.cursor = hasMask ? "pointer" : "default";
        maskBtn.classList.toggle("erpk-btn-active", masksOn);
        maskBtn.style.color = masksOn ? ACTIVE_GREEN : "rgba(255, 255, 255, 0.65)";
        maskBtn.style.borderColor = masksOn ? ACTIVE_GREEN_BORDER : "rgba(255, 255, 255, 0.14)";
        if (hideBtn._erpkHidden !== state.hideBoxes) {
            hideBtn._erpkHidden = state.hideBoxes;
            setEyeIcon(hideBtn, state.hideBoxes);
            hideBtn.dataset.tip = state.hideBoxes
                ? "Show all region overlays (H)" : "Hide all region overlays (H)";
        }
        clearBtn.disabled = !count;
        clearBtn.style.opacity = count ? "1" : "0.45";
        clearBtn.style.cursor = count ? "pointer" : "default";
        if (!count) disarmClear();
        syncRegionSockets();
        syncInspector();
    }

    // A light band sweeps the frame top to bottom while the scan runs, over a
    // slight dim so the image reads as "being processed".
    function drawScanSweep() {
        const t = (performance.now() % 1600) / 1600;
        const y = t * (state.cssH + 160) - 80;
        ctx.fillStyle = "rgba(0, 0, 0, 0.22)";
        ctx.fillRect(0, 0, state.cssW, state.cssH);
        const grad = ctx.createLinearGradient(0, y - 70, 0, y + 70);
        grad.addColorStop(0, "rgba(82, 201, 125, 0)");
        grad.addColorStop(0.5, "rgba(82, 201, 125, 0.22)");
        grad.addColorStop(1, "rgba(82, 201, 125, 0)");
        ctx.fillStyle = grad;
        ctx.fillRect(0, y - 70, state.cssW, 140);
        ctx.fillStyle = "rgba(177, 255, 207, 0.55)";
        ctx.fillRect(0, y - 1, state.cssW, 2);
    }

    // Drives render at animation rate only while a scan is in flight; the
    // loop ends itself on the final post-scan render.
    function scanFxLoop() {
        render();
        if (state.scanning) requestAnimationFrame(scanFxLoop);
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
        if (state.drag?.mode === "resize") drawResizeBadge(state.drag.box);
        if (state.scanning) drawScanSweep();
        renderStatus();
        // Keyboard mutations (delete, paste, duplicate, depth) reach the open
        // panel through the shared render path; a row drag in flight owns the
        // row DOM and must not be rebuilt under the pointer.
        if (panel && !panelRowDragging) {
            renderPanelRows();
            refreshPanelDim();
            refreshPanelDetail();
        }
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
            if (b.hidden) continue;
            if (p.x >= b.x && p.x <= b.x + b.w && p.y >= b.y && p.y <= b.y + b.h) {
                hits.push(b);
            }
        }
        return hits;
    }

    // Topmost box wins.
    // Live scale readout while resizing a scanned region: percentages are
    // relative to the origin box, making "scaled to fit" visible.
    function drawResizeBadge(box) {
        if (!box?.src) return;
        const pw = Math.round((box.w / box.src.w) * 100);
        const ph = Math.round((box.h / box.src.h) * 100);
        const text = pw === ph ? `${pw}%` : `${pw}% × ${ph}%`;
        const bx = (box.x + box.w) * state.cssW + 6;
        const by = (box.y + box.h) * state.cssH + 14;
        ctx.save();
        ctx.font = "bold 11px 'Segoe UI', sans-serif";
        const tw = ctx.measureText(text).width;
        const px = Math.min(bx, state.cssW - tw - 12);
        const py = Math.min(by, state.cssH - 6);
        ctx.fillStyle = "rgba(8, 8, 10, 0.85)";
        ctx.fillRect(px - 5, py - 11, tw + 10, 16);
        ctx.fillStyle = "rgba(255, 255, 255, 0.95)";
        ctx.fillText(text, px, py);
        ctx.restore();
    }

    // 14px transparency-checker tile, built once and shared as a pattern.
    let checkerTile = null;
    function checkerPattern(target) {
        if (!checkerTile) {
            checkerTile = document.createElement("canvas");
            checkerTile.width = 14;
            checkerTile.height = 14;
            const tctx = checkerTile.getContext("2d");
            tctx.fillStyle = "rgba(186, 186, 186, 0.92)";
            tctx.fillRect(0, 0, 14, 14);
            tctx.fillStyle = "rgba(118, 118, 118, 0.92)";
            tctx.fillRect(0, 0, 7, 7);
            tctx.fillRect(7, 7, 7, 7);
        }
        return target.createPattern(checkerTile, "repeat");
    }

    // The erase-preview at a moved region's origin: a transparency checker
    // clipped to the object's silhouette, reading as "already cut out".
    // Rebuilt only when the rendered size changes.
    function ghostCheckerFor(box, gw, gh) {
        const pw = Math.max(1, Math.round(gw));
        const ph = Math.max(1, Math.round(gh));
        const cached = box._erpkGhostChecker;
        if (cached && cached.width === pw && cached.height === ph) return cached;
        const maskImg = box._erpkMaskImg;
        if (!maskImg || !maskImg.complete || !maskImg.naturalWidth) return null;
        const off = document.createElement("canvas");
        off.width = pw;
        off.height = ph;
        const offCtx = off.getContext("2d");
        offCtx.fillStyle = checkerPattern(offCtx);
        offCtx.fillRect(0, 0, pw, ph);
        offCtx.globalCompositeOperation = "destination-in";
        offCtx.drawImage(maskImg, 0, 0, pw, ph);
        box._erpkGhostChecker = off;
        return off;
    }

    // Thin arrow from the origin's center to the displaced box's center,
    // tying the erase-preview to the destination at a glance.
    function drawMoveArrow(box, color) {
        const sx = (box.src.x + box.src.w / 2) * state.cssW;
        const sy = (box.src.y + box.src.h / 2) * state.cssH;
        const dx = (box.x + box.w / 2) * state.cssW;
        const dy = (box.y + box.h / 2) * state.cssH;
        const len = Math.hypot(dx - sx, dy - sy);
        if (len < 28) return;
        const ux = (dx - sx) / len;
        const uy = (dy - sy) / len;
        // Stop short of both centers so the arrow reads as a connector.
        const ax = sx + ux * 10;
        const ay = sy + uy * 10;
        const bx = dx - ux * 14;
        const by = dy - uy * 14;
        ctx.save();
        ctx.strokeStyle = color + "aa";
        ctx.fillStyle = color + "aa";
        ctx.lineWidth = 1.5;
        ctx.setLineDash([6, 4]);
        ctx.beginPath();
        ctx.moveTo(ax, ay);
        ctx.lineTo(bx, by);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.beginPath();
        ctx.moveTo(bx + ux * 7, by + uy * 7);
        ctx.lineTo(bx - uy * 4, by + ux * 4);
        ctx.lineTo(bx + uy * 4, by - ux * 4);
        ctx.closePath();
        ctx.fill();
        ctx.restore();
    }

    // True when the region's geometry has left its scan origin box.
    function regionMoved(box) {
        if (!box.src) return false;
        return ["x", "y", "w", "h"].some(
            (k) => Math.abs(box.src[k] - box[k]) > 0.005,
        );
    }

    // The masked object pixels cropped from the source image at the origin
    // box, for the drag preview of a moved region. Built once per region.
    function cutoutFor(box) {
        if (box._erpkCutout) return box._erpkCutout;
        const img = upstreamImage("image");
        if (!img || !img.complete || !img.naturalWidth) return null;
        let maskImg = box._erpkMaskImg;
        if (!maskImg) {
            maskImg = new Image();
            maskImg.src = "data:image/png;base64," + box.mask;
            box._erpkMaskImg = maskImg;
        }
        if (!maskImg.complete || !maskImg.naturalWidth) {
            maskImg.addEventListener("load", () => render(), { once: true });
            return null;
        }
        const pw = Math.max(1, Math.round(box.src.w * img.naturalWidth));
        const ph = Math.max(1, Math.round(box.src.h * img.naturalHeight));
        const off = document.createElement("canvas");
        off.width = pw;
        off.height = ph;
        const offCtx = off.getContext("2d");
        offCtx.drawImage(
            img,
            box.src.x * img.naturalWidth, box.src.y * img.naturalHeight,
            pw, ph, 0, 0, pw, ph,
        );
        offCtx.globalCompositeOperation = "destination-in";
        offCtx.drawImage(maskImg, 0, 0, pw, ph);
        box._erpkCutout = off;
        return off;
    }

    // True when the region's segmentation covers the point, false when the
    // point falls in the empty part of the mask, null when there is no usable
    // mask. Pixel data decodes once per region into a cached ImageData.
    function maskPixelHit(box, p) {
        if (!box.mask) return null;
        let img = box._erpkMaskImg;
        if (!img) {
            img = new Image();
            img.src = "data:image/png;base64," + box.mask;
            box._erpkMaskImg = img;
        }
        if (!img.complete || !img.naturalWidth) return null;
        if (!box._erpkMaskData) {
            const off = document.createElement("canvas");
            off.width = img.naturalWidth;
            off.height = img.naturalHeight;
            const offCtx = off.getContext("2d", { willReadFrequently: true });
            offCtx.drawImage(img, 0, 0);
            box._erpkMaskData = offCtx.getImageData(0, 0, off.width, off.height);
        }
        const u = (p.x - box.x) / box.w;
        const v = (p.y - box.y) / box.h;
        if (u < 0 || u > 1 || v < 0 || v > 1) return false;
        const data = box._erpkMaskData;
        const col = Math.min(data.width - 1, Math.floor(u * data.width));
        const row = Math.min(data.height - 1, Math.floor(v * data.height));
        return data.data[(row * data.width + col) * 4] > 127;
    }

    // Front-to-back pick that lets clicks pass through the empty part of a
    // scanned region's mask: a maskless region keeps plain rectangle
    // semantics, a masked one claims the point only where its object is.
    // A SELECTED region keeps its whole rectangle, so grabbing near a corner
    // handle manipulates it instead of falling through and starting a new box.
    function maskAwareHit(p) {
        if (state.hideBoxes) return -1;
        const hits = boxesAt(p);
        if (!hits.length) return -1;
        for (const box of hits) {
            if (state.selection.has(box) || maskPixelHit(box, p) !== false) {
                return state.boxes.indexOf(box);
            }
        }
        return state.boxes.indexOf(hits[0]);
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
        const hit = maskAwareHit(pointerNorm(e));
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

    // Socket families: desc_N strings override a region's description, ref_N
    // images attach a numbered reference. A connected socket owns its
    // region's slot; the node face only carries sockets that are exposed or
    // wired, since the Vue renderer ignores input.hidden, so unexposed
    // sockets are physically removed and re-added on demand (removeInput
    // fixes up link slot indices; wired sockets are never removed). Labels
    // carry the region's text so a depth reorder visibly remaps the wires.
    const SOCKET_FAMILIES = {
        desc: { ioType: "STRING", max: REGION_DESC_INPUTS, key: "erpk_region_desc" },
        ref: { ioType: "IMAGE", max: REGION_REF_INPUTS, key: "erpk_region_ref" },
    };

    function socketWiredFor(prefix, box) {
        const index = state.boxes.indexOf(box);
        if (index < 0) return false;
        const input = node.inputs?.find((i) => i.name === `${prefix}_${index + 1}`);
        return input?.link != null;
    }

    function exposedSocketSet(prefix) {
        const saved = node.properties?.[SOCKET_FAMILIES[prefix].key];
        return new Set(Array.isArray(saved) ? saved : []);
    }

    function persistExposedSockets(prefix, set) {
        if (!node.properties) node.properties = {};
        node.properties[SOCKET_FAMILIES[prefix].key] = [...set].sort((a, b) => a - b);
    }

    function syncFamilySockets(prefix) {
        if (!node.inputs) return;
        const family = SOCKET_FAMILIES[prefix];
        const pattern = new RegExp(`^${prefix}_(\\d+)$`);
        const exposed = exposedSocketSet(prefix);
        let changed = false;
        for (const input of node.inputs) {
            const match = input.name?.match(pattern);
            if (match && input.link != null && !exposed.has(+match[1])) {
                exposed.add(+match[1]);
                changed = true;
            }
        }
        for (let i = node.inputs.length - 1; i >= 0; i--) {
            const input = node.inputs[i];
            const match = input.name?.match(pattern);
            if (match && !exposed.has(+match[1]) && input.link == null) {
                node.removeInput(i);
            }
        }
        for (const n of [...exposed].sort((a, b) => a - b)) {
            if (n < 1 || n > family.max) continue;
            if (!node.inputs.some((i) => i.name === `${prefix}_${n}`)) {
                node.addInput(`${prefix}_${n}`, family.ioType);
            }
        }
        for (const input of node.inputs) {
            const match = input.name?.match(pattern);
            if (!match) continue;
            const n = +match[1];
            const box = state.boxes[n - 1];
            const text = box ? (box.desc || box.text || `region ${n}`) : "unused";
            input.label = `${prefix} ${n} · ${text.length > 18 ? text.slice(0, 17) + "…" : text}`;
        }
        if (changed) persistExposedSockets(prefix, exposed);
        const computed = node.computeSize?.();
        if (computed && node.size[1] < computed[1]) {
            node.setSize([node.size[0], computed[1]]);
        }
    }

    function toggleFamilySocket(prefix) {
        const index = primaryIndex();
        if (index < 0 || index >= SOCKET_FAMILIES[prefix].max) return;
        if (socketWiredFor(prefix, state.primary)) return;
        const n = index + 1;
        const exposed = exposedSocketSet(prefix);
        if (exposed.has(n)) exposed.delete(n);
        else exposed.add(n);
        persistExposedSockets(prefix, exposed);
        syncFamilySockets(prefix);
        node.setDirtyCanvas?.(true, true);
        render();
    }

    function descWiredFor(box) {
        return socketWiredFor("desc", box);
    }

    function refWiredFor(box) {
        return socketWiredFor("ref", box);
    }

    function syncRegionSockets() {
        syncFamilySockets("desc");
        syncFamilySockets("ref");
    }

    function onPlugToggle() {
        toggleFamilySocket("desc");
    }

    function onRefToggle() {
        toggleFamilySocket("ref");
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
        const plugged = wireable && (wired || exposedSocketSet("desc").has(index + 1));
        plugBtn.disabled = !wireable || wired;
        plugBtn.style.opacity = wireable ? "1" : "0.45";
        plugBtn.classList.toggle("erpk-btn-active", plugged);
        plugBtn.style.color = plugged
            ? ACTIVE_GREEN : "rgba(255, 255, 255, 0.65)";
        plugBtn.style.borderColor = plugged
            ? ACTIVE_GREEN_BORDER : "rgba(255, 255, 255, 0.14)";
        plugBtn.dataset.tip = wired
            ? "Description is wired — disconnect the input to unplug"
            : plugged
                ? "Hide this region's description input"
                : wireable
                    ? "Expose this region's description as an input"
                    : "Only regions 1–10 can take a description input";
        const refWired = !!box && refWiredFor(box);
        const refWireable = index >= 0 && index < REGION_REF_INPUTS;
        const refPlugged = refWireable
            && (refWired || exposedSocketSet("ref").has(index + 1));
        refBtn.disabled = !refWireable || refWired;
        refBtn.style.opacity = refWireable ? "1" : "0.45";
        refBtn.classList.toggle("erpk-btn-active", refPlugged);
        refBtn.style.color = refPlugged
            ? ACTIVE_GREEN : "rgba(255, 255, 255, 0.65)";
        refBtn.style.borderColor = refPlugged
            ? ACTIVE_GREEN_BORDER : "rgba(255, 255, 255, 0.14)";
        refBtn.dataset.tip = refWired
            ? "Reference image is wired — disconnect the input to unplug"
            : refPlugged
                ? "Hide this region's reference image input"
                : refWireable
                    ? "Attach a reference image input to this region"
                    : "Only regions 1–10 can take a reference image input";
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
            const hit = maskAwareHit(p);
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
            state.drag = {
                mode: "resize", box,
                anchor: resizeAnchor(box, handleId),
                // Aspect at grab time, for Shift-constrained resizing.
                aspect: box.h > 0 ? box.w / box.h : 1,
            };
        } else {
            const hit = maskAwareHit(p);
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
                // Clicking a moved region's erase-preview ghost cancels the
                // move: the region snaps back to its origin.
                const ghost = state.hideBoxes ? null : state.boxes.find(
                    (b) => b.mask && regionMoved(b)
                        && p.x >= b.src.x && p.x <= b.src.x + b.src.w
                        && p.y >= b.src.y && p.y <= b.src.y + b.src.h,
                );
                if (ghost) {
                    Object.assign(ghost, {
                        x: ghost.src.x, y: ghost.src.y,
                        w: ghost.src.w, h: ghost.src.h,
                    });
                    select(ghost);
                    syncWidget();
                    render();
                    return;
                }
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
            trackRegionTip(e);
            const hover = maskAwareHit(pointerNorm(e));
            if (hover !== state.hoverIndex) {
                state.hoverIndex = hover;
                render();
            }
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
            let corner = snapPoint(p);
            // Shift constrains to the aspect the box had when grabbed; the
            // larger drag axis wins so the gesture feels dominant-direction.
            if (e.shiftKey && d.aspect > 0) {
                const dx = corner.x - d.anchor.x;
                const dy = corner.y - d.anchor.y;
                let aw = Math.abs(dx);
                let ah = Math.abs(dy);
                if (aw / Math.max(ah, 1e-6) > d.aspect) ah = aw / d.aspect;
                else aw = ah * d.aspect;
                corner = {
                    x: clamp(d.anchor.x + Math.sign(dx || 1) * aw, 0, 1),
                    y: clamp(d.anchor.y + Math.sign(dy || 1) * ah, 0, 1),
                };
            }
            Object.assign(d.box, rectFrom(d.anchor, corner));
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
        const hit = maskAwareHit(pointerNorm(e));
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
        if (mod && key === "z") {
            e.preventDefault();
            e.stopPropagation();
            if (e.shiftKey) redoRegions();
            else undoRegions();
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
        // Arrow nudging in frame pixels: 1px, 10px with Shift; Alt resizes
        // instead of moving. Bypasses snap — nudging IS the fine adjustment.
        const arrow = {
            ArrowLeft: [-1, 0],
            ArrowRight: [1, 0],
            ArrowUp: [0, -1],
            ArrowDown: [0, 1],
        }[e.key];
        if (arrow && state.selection.size && !state.hideBoxes && !mod) {
            e.preventDefault();
            e.stopPropagation();
            const dims = frameDims(node);
            const step = e.shiftKey ? 10 : 1;
            const dx = (arrow[0] * step) / dims.w;
            const dy = (arrow[1] * step) / dims.h;
            for (const box of state.selection) {
                if (e.altKey) {
                    box.w = clamp(box.w + dx, MIN_REGION_SIZE, 1 - box.x);
                    box.h = clamp(box.h + dy, MIN_REGION_SIZE, 1 - box.y);
                } else {
                    box.x = clamp(box.x + dx, 0, 1 - box.w);
                    box.y = clamp(box.y + dy, 0, 1 - box.h);
                }
            }
            syncWidget();
            render();
            return;
        }
        if (key === "h" && !mod && !e.altKey && !e.shiftKey) {
            e.preventDefault();
            e.stopPropagation();
            state.hideBoxes = !state.hideBoxes;
            render();
        }
        if (key === "f" && !mod && !e.altKey && !e.shiftKey) {
            e.preventDefault();
            e.stopPropagation();
            onToggleFullscreen();
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
        const on = ACTIVE_GREEN;
        const off = "rgba(255, 255, 255, 0.65)";
        const onBorder = ACTIVE_GREEN_BORDER;
        const offBorder = "rgba(255, 255, 255, 0.14)";
        gridBtn.classList.toggle("erpk-btn-active", state.gridShow);
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
        snapBtn.classList.toggle("erpk-btn-active", snapActive);
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

    // The dimension widgets' value setters relay into applyAspectChange, so
    // assigning here relayouts the canvas like a manual edit would.
    function onMatchClick() {
        const dims = matchBtn._erpkDims;
        if (!dims) return;
        const widthWidget = findWidget(node, "width");
        const heightWidget = findWidget(node, "height");
        if (widthWidget) widthWidget.value = dims.w;
        if (heightWidget) heightWidget.value = dims.h;
        node.setDirtyCanvas?.(true, true);
        render();
    }

    function onBringForward() {
        moveSelectedRegion(1);
    }

    // --- Vision scan -------------------------------------------------------
    // Replaces the canvas with the engine's objects, ordered back-to-front by
    // depth_rank so array order stays z-order. Coordinates are re-clamped and
    // degenerate boxes dropped, mirroring the Python and route-side guards;
    // mask/caption/name ride along when present.
    function applyScanResults(objects) {
        const sorted = (Array.isArray(objects) ? objects.slice() : [])
            .sort((a, b) => (Number(a?.depth_rank) || 0) - (Number(b?.depth_rank) || 0));
        const added = [];
        for (const obj of sorted) {
            const src = obj?.box;
            if (!src || typeof src !== "object") continue;
            const nums = [src.x, src.y, src.w, src.h].map((v) => Number(v ?? 0));
            if (!nums.every(Number.isFinite)) continue;
            const x = clamp(nums[0], 0, 1);
            const y = clamp(nums[1], 0, 1);
            const w = clamp(nums[2], 0, 1 - x);
            const h = clamp(nums[3], 0, 1 - y);
            if (w <= 0.005 || h <= 0.005) continue;
            const name = typeof obj.name === "string" ? obj.name : "";
            const caption = typeof obj.caption === "string" ? obj.caption : "";
            const region = {
                x, y, w, h,
                kind: "object",
                // The per-region caption feeds the generation prompt; the short
                // name is the layer label and its color family.
                desc: caption || name,
                text: "",
            };
            if (typeof obj.mask === "string" && obj.mask) region.mask = obj.mask;
            if (name) region.group = name;
            // Origin box: where the object's pixels live in the source image.
            // Moving the region away from it turns the prompt into a
            // relocation and drives the cut-out drag preview.
            region.src = { x, y, w, h };
            added.push(region);
        }
        if (!added.length) {
            state.scanError = "Scan found no objects";
            return;
        }
        // A scan replaces the canvas: clear every existing region, then drop in
        // the scanned set with nothing selected so dragging one region doesn't
        // drag them all. One syncWidget keeps the replace a single undo step.
        state.boxes = added;
        state.selection = new Set();
        state.primary = null;
        syncWidget();
    }

    async function onScanClick() {
        if (state.scanning) return;
        const model = node.properties?.erpkScanModel;
        const img = upstreamImage("image");
        if (!img || !img.complete || !img.naturalWidth) {
            state.scanError = "No loaded image to scan";
            render();
            return;
        }
        // Draw the already-loaded image into an offscreen canvas; toDataURL
        // taints and throws on a cross-origin source, which we surface.
        // Downscaled JPEG: vision models resample internally, so full-res
        // lossless uploads only cost bandwidth; white fill keeps any alpha
        // from encoding as black.
        let dataUrl;
        try {
            const scale = Math.min(1, SCAN_MAX_EDGE_PX / Math.max(img.naturalWidth, img.naturalHeight));
            const off = document.createElement("canvas");
            off.width = Math.max(1, Math.round(img.naturalWidth * scale));
            off.height = Math.max(1, Math.round(img.naturalHeight * scale));
            const offCtx = off.getContext("2d");
            offCtx.fillStyle = "#fff";
            offCtx.fillRect(0, 0, off.width, off.height);
            offCtx.drawImage(img, 0, 0, off.width, off.height);
            dataUrl = off.toDataURL("image/jpeg", 0.85);
        } catch (err) {
            state.scanError = "Can't read image (cross-origin?)";
            render();
            return;
        }
        state.scanError = null;
        state.scanning = true;
        state.scanAbort = new AbortController();
        scanFxLoop();
        try {
            const body = { image: dataUrl, max_objects: SCAN_MAX_OBJECTS, engine: "gemini" };
            if (model) body.model = model;
            const res = await fetch("/erpk/scan", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
                signal: state.scanAbort.signal,
            });
            const json = await res.json().catch(() => ({}));
            if (!res.ok || json.error) {
                state.scanError = json.error || `Scan failed (${res.status})`;
            } else {
                applyScanResults(json.objects);
            }
        } catch (err) {
            if (err.name === "AbortError") return;
            state.scanError = `Scan failed: ${err.message}`;
        } finally {
            state.scanning = false;
            state.scanAbort = null;
            render();
        }
    }

    function onHideToggle() {
        state.hideBoxes = !state.hideBoxes;
        render();
    }

    function onMaskToggle() {
        if (!state.boxes.some((b) => b.mask)) return;
        state.showMasks = !state.showMasks;
        render();
    }

    // --- Shortcuts overlay ------------------------------------------------
    // The ? button toggles a cheat sheet anchored above the status strip;
    // outside clicks and Escape dismiss it.
    let helpPanel = null;

    function syncHelpButton() {
        const open = !!helpPanel;
        helpBtn.classList.toggle("erpk-btn-active", open);
        helpBtn.style.color = open ? ACTIVE_GREEN : "rgba(255, 255, 255, 0.65)";
        helpBtn.style.borderColor = open
            ? ACTIVE_GREEN_BORDER : "rgba(255, 255, 255, 0.14)";
    }

    function closeHelp() {
        if (!helpPanel) return;
        document.removeEventListener("pointerdown", onHelpDocPointerDown, true);
        document.removeEventListener("keydown", onHelpDocKeyDown, true);
        helpPanel.remove();
        helpPanel = null;
        syncHelpButton();
    }

    // Presses on the button itself fall through to the click toggle; closing
    // here too would make the toggle reopen on every press.
    function onHelpDocPointerDown(e) {
        if (!helpPanel || helpPanel.contains(e.target)
            || helpBtn.contains(e.target)) return;
        closeHelp();
    }

    function onHelpDocKeyDown(e) {
        if (e.key === "Escape" && helpPanel) {
            e.preventDefault();
            e.stopPropagation();
            e._erpkEscapeClosedPopover = true;
            closeHelp();
        }
    }

    function openHelp() {
        closePanel();
        helpPanel = document.createElement("div");
        helpPanel.style.position = "absolute";
        helpPanel.style.zIndex = "20";
        helpPanel.style.boxSizing = "border-box";
        helpPanel.style.padding = "4px";
        helpPanel.style.background = PANEL_BG;
        helpPanel.style.border = "1px solid " + HAIRLINE;
        helpPanel.style.borderRadius = "6px";
        helpPanel.style.boxShadow = "0 4px 14px rgba(0, 0, 0, 0.45)";
        helpPanel.style.maxHeight = Math.round(root.clientHeight * 0.8) + "px";
        helpPanel.style.overflowY = "auto";
        helpPanel.style.overflowX = "hidden";
        helpPanel.style.scrollbarWidth = "thin";
        helpPanel.style.scrollbarColor = "rgba(255, 255, 255, 0.25) transparent";

        const header = document.createElement("div");
        header.textContent = "Shortcuts";
        header.style.font = "8px 'Segoe UI', sans-serif";
        header.style.color = "rgba(255, 255, 255, 0.45)";
        header.style.padding = "2px 6px 4px";
        header.style.borderBottom = "1px solid " + HAIRLINE;
        header.style.marginBottom = "3px";
        helpPanel.appendChild(header);

        const rows = [
            ["drag", "draw a region"],
            ["Ctrl+drag", "force-draw over a region"],
            ["click", "select"],
            ["Shift+click", "add or remove from selection"],
            ["Shift+drag", "marquee select"],
            ["Shift while resizing", "keep the aspect ratio"],
            ["drag a region", "move selection"],
            ["Alt+click", "cycle overlapping regions"],
            ["double-click", "edit description in the inspector"],
            ["right-click", "region details, list, and depth order"],
            ["Del / Backspace", "delete selected"],
            ["arrow keys", "nudge 1px, Shift for 10px"],
            ["Alt+arrows", "resize 1px, Shift for 10px"],
            ["Ctrl/Cmd+C V D", "copy, paste, duplicate"],
            ["Ctrl/Cmd+Z / +Shift+Z", "undo, redo region changes"],
            ["[ and ]", "send back, bring forward"],
            ["H", "hide region overlays"],
            ["F", "expand editor, Esc to exit"],
        ];
        const grid = document.createElement("div");
        grid.style.display = "grid";
        grid.style.gridTemplateColumns = "auto 1fr";
        grid.style.gap = "3px 10px";
        grid.style.padding = "2px 6px 3px";
        grid.style.font = "8px 'Segoe UI', sans-serif";
        for (const [keys, action] of rows) {
            const key = document.createElement("span");
            key.textContent = keys;
            key.style.color = "rgba(255, 255, 255, 0.70)";
            key.style.whiteSpace = "nowrap";
            const act = document.createElement("span");
            act.textContent = action;
            act.style.color = "rgba(255, 255, 255, 0.45)";
            grid.appendChild(key);
            grid.appendChild(act);
        }
        helpPanel.appendChild(grid);
        helpPanel.addEventListener("pointerdown", onPanelPointerDown);

        root.appendChild(helpPanel);
        helpPanel.style.right = "6px";
        helpPanel.style.bottom = (root.offsetHeight - status.offsetTop + 4) + "px";

        document.addEventListener("pointerdown", onHelpDocPointerDown, true);
        document.addEventListener("keydown", onHelpDocKeyDown, true);
        syncHelpButton();
    }

    function onHelpToggle() {
        if (helpPanel) closeHelp();
        else openHelp();
    }

    // --- Scan options popover --------------------------------------------
    // The gear button opens a small popover with the scan model picker. The
    // model list is fetched once and cached; the choice persists in node
    // properties and rides along with the scan request.
    let optionsPanel = null;
    let scanModels = null;        // {models:[...], default:"..."} cached after a good fetch
    let scanModelSelect = null;

    function syncOptionsButton() {
        const open = !!optionsPanel;
        gearBtn.classList.toggle("erpk-btn-active", open);
        gearBtn.style.color = open ? ACTIVE_GREEN : "rgba(255, 255, 255, 0.65)";
        gearBtn.style.borderColor = open
            ? ACTIVE_GREEN_BORDER : "rgba(255, 255, 255, 0.14)";
    }

    function closeOptions() {
        if (!optionsPanel) return;
        document.removeEventListener("pointerdown", onOptionsDocPointerDown, true);
        document.removeEventListener("keydown", onOptionsDocKeyDown, true);
        optionsPanel.remove();
        optionsPanel = null;
        scanModelSelect = null;
        syncOptionsButton();
    }

    function onOptionsDocPointerDown(e) {
        if (!optionsPanel || optionsPanel.contains(e.target)
            || gearBtn.contains(e.target)) return;
        closeOptions();
    }

    function onOptionsDocKeyDown(e) {
        if (e.key === "Escape" && optionsPanel) {
            e.preventDefault();
            e.stopPropagation();
            e._erpkEscapeClosedPopover = true;
            closeOptions();
        }
    }

    function populateScanModels() {
        if (!scanModelSelect) return;
        scanModelSelect.textContent = "";
        if (!scanModels) {
            // Fetch failed: a value-less placeholder so selecting it persists
            // nothing (the scan then omits "model" and the server default runs).
            const opt = document.createElement("option");
            opt.value = "";
            opt.textContent = "server default (list unavailable)";
            opt.selected = true;
            scanModelSelect.appendChild(opt);
            return;
        }
        const models = scanModels.models;
        const chosen = node.properties?.erpkScanModel || scanModels.default || models[0];
        for (const m of models) {
            const opt = document.createElement("option");
            opt.value = m;
            opt.textContent = m;
            if (m === chosen) opt.selected = true;
            scanModelSelect.appendChild(opt);
        }
    }

    // Only a real response is cached; a failed fetch shows the default and
    // retries the next time the popover opens.
    async function loadScanModels() {
        if (scanModels) { populateScanModels(); return; }
        let data = null;
        try {
            const res = await fetch("/erpk/scan/models");
            const json = await res.json();
            if (json && Array.isArray(json.models) && json.models.length) data = json;
        } catch (_) { /* fall through to the default-only list */ }
        if (data) scanModels = data;
        populateScanModels();
    }

    function openOptions() {
        closePanel();
        closeHelp();
        optionsPanel = document.createElement("div");
        optionsPanel.style.position = "absolute";
        optionsPanel.style.zIndex = "20";
        optionsPanel.style.boxSizing = "border-box";
        optionsPanel.style.width = "200px";
        optionsPanel.style.padding = "6px";
        optionsPanel.style.background = PANEL_BG;
        optionsPanel.style.border = "1px solid " + HAIRLINE;
        optionsPanel.style.borderRadius = "6px";
        optionsPanel.style.boxShadow = "0 4px 14px rgba(0, 0, 0, 0.45)";

        const header = document.createElement("div");
        header.textContent = "Scan options";
        header.style.font = "8px 'Segoe UI', sans-serif";
        header.style.color = "rgba(255, 255, 255, 0.45)";
        header.style.padding = "2px 4px 4px";
        header.style.borderBottom = "1px solid " + HAIRLINE;
        header.style.marginBottom = "5px";
        optionsPanel.appendChild(header);

        const label = document.createElement("div");
        label.textContent = "Scan model";
        label.style.font = "9px 'Segoe UI', sans-serif";
        label.style.color = "rgba(255, 255, 255, 0.7)";
        label.style.padding = "0 4px 3px";
        optionsPanel.appendChild(label);

        scanModelSelect = document.createElement("select");
        styleInput(scanModelSelect);
        scanModelSelect.style.fontSize = "11px";
        scanModelSelect.addEventListener("change", () => {
            if (!node.properties) node.properties = {};
            if (scanModelSelect.value) {
                node.properties.erpkScanModel = scanModelSelect.value;
            } else {
                delete node.properties.erpkScanModel;
            }
        });
        optionsPanel.appendChild(scanModelSelect);

        const hint = document.createElement("div");
        hint.textContent = "Gemini detects the regions; SAM builds the masks.";
        hint.style.font = "8px 'Segoe UI', sans-serif";
        hint.style.color = "rgba(255, 255, 255, 0.4)";
        hint.style.padding = "5px 4px 1px";
        optionsPanel.appendChild(hint);

        optionsPanel.addEventListener("pointerdown", onPanelPointerDown);

        root.appendChild(optionsPanel);
        optionsPanel.style.right = "6px";
        optionsPanel.style.bottom = (root.offsetHeight - status.offsetTop + 4) + "px";

        loadScanModels();

        document.addEventListener("pointerdown", onOptionsDocPointerDown, true);
        document.addEventListener("keydown", onOptionsDocKeyDown, true);
        syncOptionsButton();
    }

    function onOptionsToggle() {
        if (optionsPanel) closeOptions();
        else openOptions();
    }

    // --- Tooltips ---------------------------------------------------------
    // Native title bubbles take ~1s to appear; [data-tip] elements get a
    // styled tip after a short hover, placed above the control (below when
    // clipped) and clamped inside the editor.
    const TIP_DELAY_MS = 300;
    let tipEl = null;
    let tipTimer = null;
    let tipTarget = null;
    let tipBox = null;

    function hideTip() {
        if (tipTimer) {
            clearTimeout(tipTimer);
            tipTimer = null;
        }
        tipTarget = null;
        tipBox = null;
        if (tipEl) {
            tipEl.remove();
            tipEl = null;
        }
    }

    function makeTipEl(text) {
        const el = document.createElement("div");
        el.textContent = text;
        el.style.position = "absolute";
        el.style.zIndex = "30";
        el.style.maxWidth = "240px";
        el.style.padding = "3px 7px";
        el.style.background = PANEL_BG;
        el.style.border = "1px solid " + HAIRLINE;
        el.style.borderRadius = "4px";
        el.style.boxShadow = "0 4px 14px rgba(0, 0, 0, 0.45)";
        el.style.font = "9px 'Segoe UI', sans-serif";
        el.style.lineHeight = "1.5";
        el.style.color = "rgba(255, 255, 255, 0.85)";
        el.style.whiteSpace = "pre-line";
        el.style.pointerEvents = "none";
        root.appendChild(el);
        return el;
    }

    function showTip(target) {
        const text = target.dataset.tip;
        if (!text) return;
        tipEl = makeTipEl(text);
        // Rects come in screen px; the editor lays out in its own px with
        // the graph zoom in between, so rect deltas scale back to layout px.
        const rootRect = root.getBoundingClientRect();
        if (!rootRect.width) {
            hideTip();
            return;
        }
        const scale = root.offsetWidth / rootRect.width;
        const t = target.getBoundingClientRect();
        const left = (t.left + t.width / 2 - rootRect.left) * scale
            - tipEl.offsetWidth / 2;
        const maxX = root.offsetWidth - tipEl.offsetWidth - 4;
        tipEl.style.left = Math.round(clamp(left, 4, Math.max(maxX, 4))) + "px";
        let top = (t.top - rootRect.top) * scale - tipEl.offsetHeight - 5;
        if (top < 4) top = (t.bottom - rootRect.top) * scale + 5;
        tipEl.style.top = Math.round(top) + "px";
    }

    // Regions live on the canvas, not in the DOM, so their tips anchor to
    // the pointer and are driven by the canvas hover tracking below.
    function showRegionTip(text, clientX, clientY) {
        tipEl = makeTipEl(text);
        const rootRect = root.getBoundingClientRect();
        if (!rootRect.width) {
            hideTip();
            return;
        }
        const scale = root.offsetWidth / rootRect.width;
        const px = (clientX - rootRect.left) * scale;
        const py = (clientY - rootRect.top) * scale;
        let left = px + 10;
        let top = py + 14;
        const maxX = root.offsetWidth - tipEl.offsetWidth - 4;
        const maxY = root.offsetHeight - tipEl.offsetHeight - 4;
        if (left > maxX) left = px - tipEl.offsetWidth - 10;
        if (top > maxY) top = py - tipEl.offsetHeight - 8;
        tipEl.style.left = Math.round(clamp(left, 4, Math.max(maxX, 4))) + "px";
        tipEl.style.top = Math.round(clamp(top, 4, Math.max(maxY, 4))) + "px";
    }

    function regionTipText(box) {
        const index = state.boxes.indexOf(box);
        const name = box.group || box.desc
            || (box.kind === "text" ? box.text : "") || "unnamed";
        const lines = [`#${index + 1} · ${name}`];
        // The canvas tag shows only the name; the full prompt surfaces here.
        if (box.desc && box.desc !== name) lines.push(box.desc);
        if (box.kind === "text") lines.push(`renders: "${box.text}"`);
        if (descWiredFor(box)) lines.push(`⌁ description wired from desc_${index + 1}`);
        if (refWiredFor(box)) lines.push(`▣ reference image from ref_${index + 1}`);
        return lines.join("\n");
    }

    function trackRegionTip(e) {
        const hit = maskAwareHit(pointerNorm(e));
        const box = hit >= 0 ? state.boxes[hit] : null;
        if (box === tipBox) return;
        hideTip();
        tipBox = box;
        if (!box) return;
        tipTimer = setTimeout(() => {
            tipTimer = null;
            if (state.drag || state.boxes.indexOf(box) < 0) return;
            showRegionTip(regionTipText(box), e.clientX, e.clientY);
        }, TIP_DELAY_MS);
    }

    function onCanvasTipLeave() {
        hideTip();
        if (state.hoverIndex !== -1) {
            state.hoverIndex = -1;
            render();
        }
    }

    function onTipOver(e) {
        const target = e.target.closest?.("[data-tip]");
        if (!target || target === tipTarget) return;
        hideTip();
        tipTarget = target;
        tipTimer = setTimeout(() => {
            tipTimer = null;
            showTip(target);
        }, TIP_DELAY_MS);
    }

    function onTipOut(e) {
        if (!tipTarget) return;
        if (e.relatedTarget && tipTarget.contains(e.relatedTarget)) return;
        if (tipTarget.contains(e.target)) hideTip();
    }

    root.addEventListener("pointerover", onTipOver);
    root.addEventListener("pointerout", onTipOut);
    root.addEventListener("pointerdown", hideTip, true);
    canvas.addEventListener("pointerleave", onCanvasTipLeave);

    // --- Region list panel ----------------------------------------------
    // Right-click panel listing regions front-to-back with per-row select,
    // duplicate, delete, and pointer-drag depth reordering.
    let panel = null;
    let panelList = null;
    let panelRowDragging = false;
    let panelDimFields = null;    // X/Y/W/H inputs in the region detail section
    let panelNameInput = null;    // layer name (region.group) field
    let panelDescInput = null;    // prompt (region.desc) textarea
    let panelEyeBtn = null;       // per-region hide/show toggle in the detail
    let panelThumb = null;        // mask thumbnail canvas

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
        panelDimFields = null;
        panelNameInput = null;
        panelDescInput = null;
        panelEyeBtn = null;
        panelThumb = null;
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
            e._erpkEscapeClosedPopover = true;
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
        const order = [...panelList.children]
            .filter((el) => el._erpkBox)
            .map((el) => el._erpkBox)
            .reverse();
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

    // Geometry fields at the top of the panel edit the selected region in
    // frame pixels; values apply live and follow selection changes.
    function applyPanelDim(key, input) {
        const box = state.primary;
        if (!box) return;
        const v = Number(input.value);
        if (input.value === "" || !Number.isFinite(v)) return;
        const dims = frameDims(node);
        if (key === "x") box.x = clamp(v / dims.w, 0, 1 - box.w);
        if (key === "y") box.y = clamp(v / dims.h, 0, 1 - box.h);
        if (key === "w") box.w = clamp(v / dims.w, MIN_REGION_SIZE, 1 - box.x);
        if (key === "h") box.h = clamp(v / dims.h, MIN_REGION_SIZE, 1 - box.y);
        syncWidget();
        render();
    }

    function refreshPanelDim() {
        if (!panelDimFields) return;
        const box = state.primary;
        const dims = frameDims(node);
        const px = box ? {
            x: Math.round(box.x * dims.w),
            y: Math.round(box.y * dims.h),
            w: Math.round(box.w * dims.w),
            h: Math.round(box.h * dims.h),
        } : null;
        for (const key of Object.keys(panelDimFields)) {
            const input = panelDimFields[key];
            input.disabled = !box;
            if (document.activeElement !== input) {
                input.value = px ? String(px[key]) : "";
            }
        }
    }

    // The detail section's name field edits the layer label, which also drives
    // the region's color family; clearing it drops back to the index color.
    function applyPanelName(input) {
        const box = state.primary;
        if (!box) return;
        const v = input.value.trim();
        if (v) box.group = v;
        else delete box.group;
        syncWidget();
        render();
    }

    // The prompt textarea edits region.desc, the text that feeds generation.
    function applyPanelDesc(input) {
        const box = state.primary;
        if (!box) return;
        box.desc = input.value;
        syncWidget();
        render();
    }

    // Per-region visibility: a hidden region skips drawing and hit-testing but
    // still feeds the prompt and mask outputs.
    function toggleRegionHidden(box) {
        if (!box) return;
        box.hidden = !box.hidden;
        syncWidget();
        render();
    }

    // Tinted mask silhouette in the detail thumbnail, or a flat color wash when
    // the region carries no mask.
    function drawPanelThumb(box) {
        if (!panelThumb) return;
        const tctx = panelThumb.getContext("2d");
        const w = panelThumb.width;
        const h = panelThumb.height;
        tctx.clearRect(0, 0, w, h);
        if (!box) return;
        const color = colorForRegion(box, state.boxes.indexOf(box));
        if (box.mask) {
            let m = box._erpkMaskImg;
            if (!m) {
                m = new Image();
                m.src = "data:image/png;base64," + box.mask;
                box._erpkMaskImg = m;
            }
            if (m.complete && m.naturalWidth) {
                tctx.fillStyle = color;
                tctx.fillRect(0, 0, w, h);
                tctx.globalCompositeOperation = "destination-in";
                tctx.drawImage(m, 0, 0, w, h);
                tctx.globalCompositeOperation = "source-over";
                return;
            }
            m.addEventListener("load", () => {
                if (panelThumb && state.primary === box) drawPanelThumb(box);
            }, { once: true });
        }
        tctx.fillStyle = hexToRgba(color, 0.28);
        tctx.fillRect(0, 0, w, h);
    }

    function refreshPanelDetail() {
        const box = state.primary;
        if (panelNameInput && document.activeElement !== panelNameInput) {
            panelNameInput.value = box ? (box.group || "") : "";
        }
        if (panelDescInput && document.activeElement !== panelDescInput) {
            panelDescInput.value = box ? (box.desc || "") : "";
        }
        if (panelEyeBtn) {
            const hidden = !!(box && box.hidden);
            setEyeIcon(panelEyeBtn, hidden);
            panelEyeBtn.dataset.tip = hidden ? "Show region" : "Hide region";
        }
        drawPanelThumb(box);
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
        plug.dataset.tip = "Description wired from a desc input";
        plug.textContent = "⌁";
        plug.style.display = descWiredFor(box) ? "" : "none";

        const refMark = document.createElement("span");
        refMark.style.flex = "0 0 auto";
        refMark.style.color = regionColor(index);
        refMark.dataset.tip = "Reference image wired from a ref input";
        refMark.textContent = "▣";
        refMark.style.display = refWiredFor(box) ? "" : "none";

        const label = document.createElement("span");
        label.style.flex = "1 1 auto";
        label.style.minWidth = "0";
        label.style.overflow = "hidden";
        label.style.textOverflow = "ellipsis";
        label.style.whiteSpace = "nowrap";
        // Layer name first, then the prompt, falling back to a kind + number.
        const caption = box.group || (box.kind === "text" ? box.text : box.desc);
        if (caption) {
            label.textContent = caption;
        } else {
            label.textContent = box.kind + " " + (index + 1);
            label.style.fontStyle = "italic";
            label.style.color = "rgba(255, 255, 255, 0.4)";
        }
        // A hidden region reads as dimmed in the list.
        if (box.hidden) label.style.color = "rgba(255, 255, 255, 0.35)";

        const eyeBtn = makeStripButton("");
        setEyeIcon(eyeBtn, !!box.hidden);
        eyeBtn.dataset.tip = box.hidden ? "Show region" : "Hide region";
        eyeBtn.style.fontSize = "10px";
        eyeBtn.style.padding = "0 4px";

        const dupBtn = makeStripButton("⧉");
        dupBtn.dataset.tip = "Duplicate region";
        dupBtn.style.fontSize = "10px";
        dupBtn.style.padding = "0 4px";
        const delBtn = makeStripButton("✕");
        delBtn.classList.add("erpk-btn-danger");
        delBtn.dataset.tip = "Delete region";
        delBtn.style.fontSize = "10px";
        delBtn.style.padding = "0 4px";
        delBtn.style.color = DANGER_RED_DIM;
        delBtn.style.borderColor = DANGER_RED_BORDER;

        row.appendChild(eyeBtn);
        row.appendChild(swatch);
        row.appendChild(num);
        row.appendChild(plug);
        row.appendChild(refMark);
        row.appendChild(label);
        row.appendChild(dupBtn);
        row.appendChild(delBtn);

        // Button presses must not start a row drag; their listeners die with
        // the row element on rebuild or panel close.
        eyeBtn.addEventListener("pointerdown", (e) => e.stopPropagation());
        dupBtn.addEventListener("pointerdown", (e) => e.stopPropagation());
        delBtn.addEventListener("pointerdown", (e) => e.stopPropagation());
        eyeBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            toggleRegionHidden(box);
        });
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
        closeHelp();
        // Right-clicking a region targets it: it becomes the selection and
        // the geometry fields appear; empty canvas opens just the list.
        const hit = maskAwareHit(pointerNorm(e));
        if (hit >= 0) {
            select(state.boxes[hit]);
            render();
        }
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
        header.style.display = "flex";
        header.style.alignItems = "center";
        header.style.gap = "5px";
        header.style.padding = "2px 4px 4px";
        header.style.borderBottom = "1px solid " + HAIRLINE;
        header.style.marginBottom = "3px";

        const headerLabel = document.createElement("span");
        headerLabel.textContent = "Regions · top = front";
        headerLabel.dataset.tip = "Click a row to select · drag rows to reorder "
            + "depth · the eye hides a region · ⧉ duplicates · ✕ deletes";
        headerLabel.style.flex = "1 1 auto";
        headerLabel.style.minWidth = "0";
        headerLabel.style.font = "8px 'Segoe UI', sans-serif";
        headerLabel.style.color = "rgba(255, 255, 255, 0.45)";
        headerLabel.style.whiteSpace = "nowrap";
        headerLabel.style.overflow = "hidden";
        headerLabel.style.textOverflow = "ellipsis";

        header.appendChild(headerLabel);
        panel.appendChild(header);

        // Right-clicking a region shows its detail above the list: a mask
        // thumbnail, the layer name, the X/Y/W/H pixel fields, the prompt, and
        // hide / delete actions. Empty-canvas right-clicks open just the list.
        if (hit >= 0) {
            const detail = document.createElement("div");
            detail.style.display = "flex";
            detail.style.flexDirection = "column";
            detail.style.gap = "4px";
            detail.style.padding = "2px 5px 5px";
            detail.style.marginBottom = "3px";
            detail.style.borderBottom = "1px solid " + HAIRLINE;

            const topRow = document.createElement("div");
            topRow.style.display = "flex";
            topRow.style.alignItems = "center";
            topRow.style.gap = "6px";

            panelThumb = document.createElement("canvas");
            panelThumb.width = 40;
            panelThumb.height = 40;
            panelThumb.style.flex = "0 0 auto";
            panelThumb.style.width = "40px";
            panelThumb.style.height = "40px";
            panelThumb.style.borderRadius = "3px";
            panelThumb.style.border = "1px solid " + HAIRLINE;
            panelThumb.style.background = PANEL_INPUT_BG;

            panelNameInput = document.createElement("input");
            panelNameInput.type = "text";
            panelNameInput.placeholder = "name";
            panelNameInput.dataset.tip = "Layer name — same-named regions share a color";
            styleInput(panelNameInput);
            panelNameInput.style.flex = "1 1 auto";
            panelNameInput.style.fontSize = "11px";
            panelNameInput.addEventListener("input", () => applyPanelName(panelNameInput));

            topRow.appendChild(panelThumb);
            topRow.appendChild(panelNameInput);
            detail.appendChild(topRow);

            const dimRow = document.createElement("div");
            dimRow.style.display = "flex";
            dimRow.style.alignItems = "center";
            dimRow.style.gap = "4px";
            dimRow.style.font = "8px 'Segoe UI', sans-serif";
            dimRow.style.color = "rgba(255, 255, 255, 0.45)";
            panelDimFields = {};
            for (const key of ["x", "y", "w", "h"]) {
                const label = document.createElement("span");
                label.textContent = key.toUpperCase();
                const input = document.createElement("input");
                input.type = "number";
                input.step = "1";
                styleInput(input);
                input.style.width = "38px";
                input.style.flex = "1 1 0";
                input.style.minWidth = "0";
                input.style.padding = "1px 3px";
                input.style.fontSize = "9px";
                input.addEventListener("input", () => applyPanelDim(key, input));
                panelDimFields[key] = input;
                dimRow.appendChild(label);
                dimRow.appendChild(input);
            }
            detail.appendChild(dimRow);

            panelDescInput = document.createElement("textarea");
            panelDescInput.rows = 2;
            panelDescInput.placeholder = "prompt";
            panelDescInput.dataset.tip = "Region prompt — feeds generation for this layer";
            styleInput(panelDescInput);
            panelDescInput.style.fontSize = "10px";
            panelDescInput.style.resize = "vertical";
            panelDescInput.style.minHeight = "30px";
            panelDescInput.addEventListener("input", () => applyPanelDesc(panelDescInput));
            detail.appendChild(panelDescInput);

            const actions = document.createElement("div");
            actions.style.display = "flex";
            actions.style.justifyContent = "flex-end";
            actions.style.gap = "5px";

            panelEyeBtn = makeStripButton("");
            setEyeIcon(panelEyeBtn, false);
            panelEyeBtn.style.fontSize = "11px";
            panelEyeBtn.style.padding = "0 6px";
            panelEyeBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                toggleRegionHidden(state.primary);
            });

            const detDelBtn = makeStripButton("✕");
            detDelBtn.classList.add("erpk-btn-danger");
            detDelBtn.dataset.tip = "Delete region";
            detDelBtn.style.fontSize = "11px";
            detDelBtn.style.padding = "0 6px";
            detDelBtn.style.color = DANGER_RED_DIM;
            detDelBtn.style.borderColor = DANGER_RED_BORDER;
            detDelBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                deleteRegion(state.primary);
            });

            actions.appendChild(panelEyeBtn);
            actions.appendChild(detDelBtn);
            detail.appendChild(actions);

            // Keep presses and typing inside the detail from starting a row
            // drag or reaching the canvas and ComfyUI's global hotkeys.
            detail.addEventListener("pointerdown", (e) => e.stopPropagation());
            detail.addEventListener("keydown", (e) => e.stopPropagation());
            panel.appendChild(detail);
        }

        panelList = document.createElement("div");
        panel.appendChild(panelList);
        renderPanelRows();
        refreshPanelDim();
        refreshPanelDetail();

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

    // --- Fullscreen overlay -----------------------------------------------
    // ComfyUI rewrites the DOM-widget wrapper's transform/position every frame,
    // and that transform makes the wrapper the containing block for any fixed
    // descendant. Reparenting root into document.body lifts it out of both the
    // per-frame writes and the transform so a fixed overlay resolves against
    // the viewport. Expanded state lives on root so module-level pinRootWidth
    // can see it across the closure boundary.
    let fsSaved = null;

    function syncFsButton() {
        const on = !!root._erpkExpanded;
        fsBtn.classList.toggle("erpk-btn-active", on);
        fsBtn.style.color = on ? ACTIVE_GREEN : "rgba(255, 255, 255, 0.9)";
        fsBtn.style.borderColor = on
            ? ACTIVE_GREEN_BORDER : "rgba(255, 255, 255, 0.35)";
        fsBtn.textContent = on ? "⤡" : "⤢";
        fsBtn.dataset.tip = on
            ? "Restore the editor to the node (F · Esc to exit)"
            : "Expand the editor to fill the window (F · Esc to exit)";
    }

    // Capture phase so it sees Escape regardless of focus. Each Escape goes
    // to one consumer: an open popover (the live check covers popovers that
    // register after this handler; the event marker covers ones that ran
    // before it on this same event), then a focused text field (blur), and
    // only then the overlay itself.
    function onFsDocKeyDown(e) {
        if (e.key !== "Escape" || !root._erpkExpanded) return;
        if (e._erpkEscapeClosedPopover || helpPanel || panel) return;
        const field = document.activeElement;
        if (field && root.contains(field)
            && (field.tagName === "INPUT" || field.tagName === "TEXTAREA")) {
            e.preventDefault();
            e.stopPropagation();
            field.blur();
            return;
        }
        e.preventDefault();
        e.stopPropagation();
        collapse();
    }

    function expand() {
        if (root._erpkExpanded) return;
        fsSaved = {
            parent: root.parentNode,
            nextSibling: root.nextSibling,
            position: root.style.position,
            inset: root.style.inset,
            width: root.style.width,
            maxWidth: root.style.maxWidth,
            height: root.style.height,
            zIndex: root.style.zIndex,
            bodyOverflow: document.body.style.overflow,
        };
        root._erpkExpanded = true;
        document.body.appendChild(root);
        root.style.position = "fixed";
        root.style.inset = "0";
        root.style.width = "100vw";
        root.style.maxWidth = "100vw";
        root.style.height = "100vh";
        root.style.zIndex = "9999";
        document.body.style.overflow = "hidden";
        document.addEventListener("keydown", onFsDocKeyDown, true);
        syncFsButton();
        // Entry via the button leaves focus on the button; hand it to the
        // canvas so F toggles back out.
        canvas.focus();
        requestAnimationFrame(() => layout());
    }

    function collapse() {
        if (!root._erpkExpanded) return;
        root._erpkExpanded = false;
        document.removeEventListener("keydown", onFsDocKeyDown, true);
        document.body.style.overflow = fsSaved.bodyOverflow;
        root.style.position = fsSaved.position;
        root.style.inset = fsSaved.inset;
        root.style.width = fsSaved.width;
        root.style.maxWidth = fsSaved.maxWidth;
        root.style.height = fsSaved.height;
        root.style.zIndex = fsSaved.zIndex;
        const parent = fsSaved.parent;
        if (parent) {
            const ref = fsSaved.nextSibling && fsSaved.nextSibling.parentNode === parent
                ? fsSaved.nextSibling : null;
            parent.insertBefore(root, ref);
        }
        fsSaved = null;
        syncFsButton();
        pinRootWidth(node);
        requestAnimationFrame(() => layout());
    }

    function onToggleFullscreen() {
        if (root._erpkExpanded) collapse();
        else expand();
    }

    canvas.addEventListener("pointerdown", onPointerDown);
    canvas.addEventListener("pointermove", onPointerMove);
    canvas.addEventListener("pointerup", onPointerUp);
    canvas.addEventListener("pointercancel", onPointerUp);
    canvas.addEventListener("dblclick", onDblClick);
    canvas.addEventListener("keydown", onKeyDown);
    canvas.addEventListener("contextmenu", onContextMenu);
    helpBtn.addEventListener("click", onHelpToggle);
    gearBtn.addEventListener("click", onOptionsToggle);
    fsBtn.addEventListener("click", onToggleFullscreen);
    inspector.addEventListener("pointerdown", onInspectorPointerDown);
    inspector.addEventListener("keydown", onInspectorKeyDown);
    descInput.addEventListener("input", onDescInput);
    kindSelect.addEventListener("change", onKindChange);
    textInput.addEventListener("input", onTextInput);
    clearBtn.addEventListener("click", onClearClick);
    matchBtn.addEventListener("click", onMatchClick);
    backBtn.addEventListener("click", onSendBack);
    frontBtn.addEventListener("click", onBringForward);
    plugBtn.addEventListener("click", onPlugToggle);
    refBtn.addEventListener("click", onRefToggle);
    gridBtn.addEventListener("click", onGridToggle);
    gridSizeInput.addEventListener("input", onGridSizeInput);
    gridSizeInput.addEventListener("blur", onGridSizeBlur);
    gridSizeInput.addEventListener("keydown", onGridSizeKeyDown);
    gridColorInput.addEventListener("input", onGridColorInput);
    gridAlphaInput.addEventListener("input", onGridAlphaInput);
    gridAlphaInput.addEventListener("blur", onGridAlphaBlur);
    gridAlphaInput.addEventListener("keydown", onGridSizeKeyDown);
    snapBtn.addEventListener("click", onSnapToggle);
    scanBtn.addEventListener("click", onScanClick);
    maskBtn.addEventListener("click", onMaskToggle);
    hideBtn.addEventListener("click", onHideToggle);

    const observer = new ResizeObserver(() => layout());
    observer.observe(stage);

    function setup() {
        hideRegionsWidget();
        hookDimensionWidget("width");
        hookDimensionWidget("height");
        restoreGridPrefs();
        syncRegionSockets();
    }

    function destroy() {
        // Exit expand mode first so the document Escape listener and the body
        // overflow style are dropped even if the node is removed while expanded.
        collapse();
        observer.disconnect();
        canvas.removeEventListener("pointerdown", onPointerDown);
        canvas.removeEventListener("pointermove", onPointerMove);
        canvas.removeEventListener("pointerup", onPointerUp);
        canvas.removeEventListener("pointercancel", onPointerUp);
        canvas.removeEventListener("dblclick", onDblClick);
        canvas.removeEventListener("keydown", onKeyDown);
        canvas.removeEventListener("contextmenu", onContextMenu);
        helpBtn.removeEventListener("click", onHelpToggle);
        gearBtn.removeEventListener("click", onOptionsToggle);
        fsBtn.removeEventListener("click", onToggleFullscreen);
        inspector.removeEventListener("pointerdown", onInspectorPointerDown);
        inspector.removeEventListener("keydown", onInspectorKeyDown);
        descInput.removeEventListener("input", onDescInput);
        kindSelect.removeEventListener("change", onKindChange);
        textInput.removeEventListener("input", onTextInput);
        clearBtn.removeEventListener("click", onClearClick);
        matchBtn.removeEventListener("click", onMatchClick);
        backBtn.removeEventListener("click", onSendBack);
        frontBtn.removeEventListener("click", onBringForward);
        plugBtn.removeEventListener("click", onPlugToggle);
        refBtn.removeEventListener("click", onRefToggle);
        gridBtn.removeEventListener("click", onGridToggle);
        gridSizeInput.removeEventListener("input", onGridSizeInput);
        gridSizeInput.removeEventListener("blur", onGridSizeBlur);
        gridSizeInput.removeEventListener("keydown", onGridSizeKeyDown);
        gridColorInput.removeEventListener("input", onGridColorInput);
        gridAlphaInput.removeEventListener("input", onGridAlphaInput);
        gridAlphaInput.removeEventListener("blur", onGridAlphaBlur);
        gridAlphaInput.removeEventListener("keydown", onGridSizeKeyDown);
        snapBtn.removeEventListener("click", onSnapToggle);
        scanBtn.removeEventListener("click", onScanClick);
        maskBtn.removeEventListener("click", onMaskToggle);
        state.scanAbort?.abort();
        root.removeEventListener("pointerover", onTipOver);
        root.removeEventListener("pointerout", onTipOut);
        root.removeEventListener("pointerdown", hideTip, true);
        canvas.removeEventListener("pointerleave", onCanvasTipLeave);
        hideTip();
        closePanel();
        closeHelp();
        closeOptions();
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
