// ABOUTME: Builds one region editor for a node — DOM scaffold, shared context, module wiring, lifecycle.
// ABOUTME: createRegionEditor assembles store/sockets/renderer/tools/properties/layers/toolbar over one E context.
// @ts-check

import { createState, installStore } from "./store.js";
import { installSockets } from "./sockets.js";
import { installRenderer } from "./renderer.js";
import { installTools } from "./tools.js";
import { installProperties } from "./properties.js";
import { installLayers } from "./layers.js";
import { installToolbar } from "./toolbar.js";
import {
    makeStripButton, styleInput, setEyeIcon, labelControlsFromTips, sizeIconButton,
} from "./styles.js";
import { findWidget, setWidgetHidden } from "./node_access.js";
import {
    STATUS_STRIP_H,
    INSPECTOR_H,
    GRID_MIN_CELL_PX,
    GRID_MAX_CELL_PX,
    GRID_DEFAULT_COLOR,
    STAGE_BG,
    PANEL_BG,
    HAIRLINE,
    DANGER_RED_DIM,
    DANGER_RED_BORDER,
    CONTRAST_SVG,
    GRID_SVG,
    CROSSHAIR_SVG,
    HELP_SVG,
    SETTINGS_SVG,
    SPARKLES_SVG,
    MAXIMIZE_SVG,
    CHEVRON_DOWN_SVG,
    CHEVRON_UP_SVG,
} from "./constants.js";

export function createRegionEditor(node) {
    const state = createState();

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
    // ComfyUI's ChangeTracker binds window-capture keydown at app init —
    // before any widget can — and runs its undo in a requestAnimationFrame,
    // so no listener ordering can block it. Its guard, however, skips any
    // focused element whose `type` reads "textarea" (duck-typed input
    // check); this expando makes the focused canvas pass that guard so the
    // editor's own undo stack owns Ctrl/Cmd+Z, not the graph's.
    (/** @type {any} */ (canvas)).type = "textarea";
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

    const gridBtn = sizeIconButton(makeStripButton(""));
    gridBtn.innerHTML = GRID_SVG;
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
    const snapBtn = sizeIconButton(makeStripButton(""));
    snapBtn.innerHTML = CROSSHAIR_SVG;
    snapBtn.dataset.tip = "Snap drawing, moving, and resizing to the grid";
    const helpBtn = sizeIconButton(makeStripButton(""));
    helpBtn.innerHTML = HELP_SVG;
    helpBtn.dataset.tip = "Keyboard and mouse shortcuts";
    const gearBtn = sizeIconButton(makeStripButton(""));
    gearBtn.innerHTML = SETTINGS_SVG;
    gearBtn.dataset.tip = "Scan options";
    const fsBtn = makeStripButton("");
    fsBtn.innerHTML = MAXIMIZE_SVG;
    fsBtn.dataset.tip = "Expand the editor to fill the window (F · Esc to exit)";
    floatOnStage(fsBtn, "right");
    const matchBtn = makeStripButton("⚠ match");
    matchBtn.style.font = "bold 9px 'Segoe UI', sans-serif";
    matchBtn.style.color = "rgba(249, 168, 38, 0.85)";
    matchBtn.style.borderColor = "rgba(249, 168, 38, 0.45)";
    matchBtn.style.display = "none";
    // Toggles the segmentation-mask overlay; enabled only when a region
    // actually carries a scanned mask.
    const maskBtn = sizeIconButton(makeStripButton(""));
    maskBtn.innerHTML = CONTRAST_SVG;
    maskBtn.dataset.tip = "Show segmentation masks";
    // Global overlay visibility, the strip twin of the H shortcut.
    const hideBtn = sizeIconButton(makeStripButton(""));
    setEyeIcon(hideBtn, false);
    hideBtn.dataset.tip = "Hide all region overlays (H)";
    // Scans the connected image for objects. Floats in the stage's upper-left
    // rather than the strip, and only shows when an image is connected.
    const scanBtn = makeStripButton("");
    scanBtn.innerHTML = SPARKLES_SVG;
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

    const backBtn = sizeIconButton(makeStripButton(""));
    backBtn.innerHTML = CHEVRON_DOWN_SVG;
    backBtn.dataset.tip = "Send back — one layer toward the background ( [ )";
    const frontBtn = sizeIconButton(makeStripButton(""));
    frontBtn.innerHTML = CHEVRON_UP_SVG;
    frontBtn.dataset.tip = "Bring forward — one layer toward the front ( ] )";

    inspector.appendChild(descInput);
    inspector.appendChild(kindSelect);
    inspector.appendChild(textInput);
    inspector.appendChild(backBtn);
    inspector.appendChild(frontBtn);
    root.insertBefore(inspector, status);

    // --- Shared context injected into every module --------------------
    const E = {
        node,
        state,
        root,
        stage,
        canvas,
        ctx2d: ctx,
        status,
        statusLeft,
        statusRight,
        inspector,
        descInput,
        kindSelect,
        textInput,
        backBtn,
        frontBtn,
        gridBtn,
        gridSizeInput,
        gridColorInput,
        gridAlphaInput,
        snapBtn,
        helpBtn,
        gearBtn,
        fsBtn,
        matchBtn,
        maskBtn,
        hideBtn,
        scanBtn,
        clearBtn,
        // Right-click panel state, shared so the renderer can skip rebuilding
        // the open panel mid-drag and the detail fields can be cleared on close.
        panel: null,
        panelRowDragging: false,
        panelDimFields: null,
        panelNameInput: null,
        panelDescInput: null,
        panelEyeBtn: null,
        panelThumb: null,
        panelKindBtns: null,
        panelTextLabel: null,
        panelTextInput: null,
        panelPlugBtn: null,
        panelRefBtn: null,
        panelScanBtn: null,
    };

    installStore(E);
    installSockets(E);
    installRenderer(E);
    installTools(E);
    installProperties(E);
    installLayers(E);
    installToolbar(E);

    // Name the now-assembled controls for screen readers (the icons announce as
    // nothing); the right-click panel labels its own rows as it builds them.
    labelControlsFromTips(root);

    // --- Widget plumbing ----------------------------------------------
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
        E.layout();
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

    // --- Event wiring -------------------------------------------------
    canvas.addEventListener("pointerdown", E.onPointerDown);
    canvas.addEventListener("pointermove", E.onPointerMove);
    canvas.addEventListener("pointerup", E.onPointerUp);
    canvas.addEventListener("pointercancel", E.onPointerUp);
    canvas.addEventListener("dblclick", E.onDblClick);
    canvas.addEventListener("keydown", E.onKeyDown);
    window.addEventListener("keydown", E.onGlobalUndoKey, true);
    canvas.addEventListener("contextmenu", E.onContextMenu);
    helpBtn.addEventListener("click", E.onHelpToggle);
    gearBtn.addEventListener("click", E.onOptionsToggle);
    fsBtn.addEventListener("click", E.onToggleFullscreen);
    inspector.addEventListener("pointerdown", E.onInspectorPointerDown);
    inspector.addEventListener("keydown", E.onInspectorKeyDown);
    descInput.addEventListener("input", E.onDescInput);
    kindSelect.addEventListener("change", E.onKindChange);
    textInput.addEventListener("input", E.onTextInput);
    clearBtn.addEventListener("click", E.onClearClick);
    matchBtn.addEventListener("click", E.onMatchClick);
    backBtn.addEventListener("click", E.onSendBack);
    frontBtn.addEventListener("click", E.onBringForward);
    gridBtn.addEventListener("click", E.onGridToggle);
    gridSizeInput.addEventListener("input", E.onGridSizeInput);
    gridSizeInput.addEventListener("blur", E.onGridSizeBlur);
    gridSizeInput.addEventListener("keydown", E.onGridSizeKeyDown);
    gridColorInput.addEventListener("input", E.onGridColorInput);
    gridAlphaInput.addEventListener("input", E.onGridAlphaInput);
    gridAlphaInput.addEventListener("blur", E.onGridAlphaBlur);
    gridAlphaInput.addEventListener("keydown", E.onGridSizeKeyDown);
    snapBtn.addEventListener("click", E.onSnapToggle);
    scanBtn.addEventListener("click", E.onScanClick);
    maskBtn.addEventListener("click", E.onMaskToggle);
    hideBtn.addEventListener("click", E.onHideToggle);

    root.addEventListener("pointerover", E.onTipOver);
    root.addEventListener("pointerout", E.onTipOut);
    root.addEventListener("pointerdown", E.hideTip, true);
    canvas.addEventListener("pointerleave", E.onCanvasTipLeave);

    const observer = new ResizeObserver(() => E.layout());
    observer.observe(stage);

    function setup() {
        hideRegionsWidget();
        hookDimensionWidget("width");
        hookDimensionWidget("height");
        E.restoreGridPrefs();
        E.syncRegionSockets();
    }

    function destroy() {
        // Exit expand mode first so the document Escape listener and the body
        // overflow style are dropped even if the node is removed while expanded.
        E.collapse();
        observer.disconnect();
        canvas.removeEventListener("pointerdown", E.onPointerDown);
        canvas.removeEventListener("pointermove", E.onPointerMove);
        canvas.removeEventListener("pointerup", E.onPointerUp);
        canvas.removeEventListener("pointercancel", E.onPointerUp);
        canvas.removeEventListener("dblclick", E.onDblClick);
        canvas.removeEventListener("keydown", E.onKeyDown);
        canvas.removeEventListener("contextmenu", E.onContextMenu);
        helpBtn.removeEventListener("click", E.onHelpToggle);
        gearBtn.removeEventListener("click", E.onOptionsToggle);
        fsBtn.removeEventListener("click", E.onToggleFullscreen);
        inspector.removeEventListener("pointerdown", E.onInspectorPointerDown);
        inspector.removeEventListener("keydown", E.onInspectorKeyDown);
        descInput.removeEventListener("input", E.onDescInput);
        kindSelect.removeEventListener("change", E.onKindChange);
        textInput.removeEventListener("input", E.onTextInput);
        clearBtn.removeEventListener("click", E.onClearClick);
        matchBtn.removeEventListener("click", E.onMatchClick);
        backBtn.removeEventListener("click", E.onSendBack);
        frontBtn.removeEventListener("click", E.onBringForward);
        gridBtn.removeEventListener("click", E.onGridToggle);
        gridSizeInput.removeEventListener("input", E.onGridSizeInput);
        gridSizeInput.removeEventListener("blur", E.onGridSizeBlur);
        gridSizeInput.removeEventListener("keydown", E.onGridSizeKeyDown);
        gridColorInput.removeEventListener("input", E.onGridColorInput);
        gridAlphaInput.removeEventListener("input", E.onGridAlphaInput);
        gridAlphaInput.removeEventListener("blur", E.onGridAlphaBlur);
        gridAlphaInput.removeEventListener("keydown", E.onGridSizeKeyDown);
        snapBtn.removeEventListener("click", E.onSnapToggle);
        scanBtn.removeEventListener("click", E.onScanClick);
        maskBtn.removeEventListener("click", E.onMaskToggle);
        state.scanAbort?.abort();
        root.removeEventListener("pointerover", E.onTipOver);
        root.removeEventListener("pointerout", E.onTipOut);
        root.removeEventListener("pointerdown", E.hideTip, true);
        canvas.removeEventListener("pointerleave", E.onCanvasTipLeave);
        window.removeEventListener("keydown", E.onGlobalUndoKey, true);
        E.hideTip();
        E.closePanel();
        E.closeHelp();
        E.closeOptions();
        E.disarmClear();
    }

    return {
        root,
        setup,
        loadFromWidget: E.loadFromWidget,
        layout: E.layout,
        destroy,
    };
}
