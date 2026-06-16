// ABOUTME: Editor chrome around the canvas — status-strip controls, vision scan, popovers, tooltips, fullscreen.
// ABOUTME: Owns grid/snap/clear/depth/match/hide/mask buttons; shared state and rendering reach in through E.
// @ts-check

import { clamp } from "./geometry.js";
import { frameDims, findWidget, upstreamImage, pinRootWidth } from "./node_access.js";
import {
    costLine,
    postScanWithTimeout,
    fetchScanModels,
    fetchScanSegmenters,
} from "./scanClient.js";
import { styleInput } from "./styles.js";
import {
    ACTIVE_GREEN,
    ACTIVE_GREEN_BORDER,
    DANGER_RED,
    DANGER_RED_DIM,
    DANGER_RED_BORDER,
    PANEL_BG,
    HAIRLINE,
    GRID_MIN_CELL_PX,
    GRID_MAX_CELL_PX,
    SCAN_MAX_EDGE_PX,
    SCAN_MAX_OBJECTS,
    MAXIMIZE_SVG,
    MINIMIZE_SVG,
} from "./constants.js";

export function installToolbar(E) {
    const { node, state, root, status, canvas,
            gridBtn, gridSizeInput, gridColorInput, gridAlphaInput, snapBtn,
            clearBtn, matchBtn, helpBtn, gearBtn, fsBtn } = E;

    // --- Grid & snap ------------------------------------------------------
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
        E.render();
    }

    function onGridSizeInput() {
        const v = Math.round(Number(gridSizeInput.value));
        if (!Number.isFinite(v)) return;
        state.gridCellPx = clamp(v, GRID_MIN_CELL_PX, GRID_MAX_CELL_PX);
        persistGridPrefs();
        E.render();
    }

    function onGridSizeBlur() {
        gridSizeInput.value = String(state.gridCellPx);
    }

    function onGridColorInput() {
        state.gridColor = gridColorInput.value;
        persistGridPrefs();
        E.render();
    }

    function onGridAlphaInput() {
        const v = Math.round(Number(gridAlphaInput.value));
        if (!Number.isFinite(v)) return;
        state.gridAlpha = clamp(v, 5, 100) / 100;
        persistGridPrefs();
        E.render();
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
        E.render();
    }

    // --- Clear all --------------------------------------------------------
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
        E.clearSelection();
        E.syncWidget();
        E.render();
    }

    // --- Depth & match ----------------------------------------------------
    function onSendBack() {
        E.moveSelectedRegion(-1);
    }

    function onBringForward() {
        E.moveSelectedRegion(1);
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
        E.render();
    }

    // --- Vision scan ------------------------------------------------------
    // A transient flash inside the editor root (which also is the fullscreen
    // overlay, so the toast follows into expanded mode). Self-contained so it
    // never depends on ComfyUI's cross-version toast service.
    let costToast = null;
    let costToastTimer = null;

    function showCostToast(text) {
        if (costToast) costToast.remove();
        if (costToastTimer) clearTimeout(costToastTimer);
        const toast = document.createElement("div");
        toast.textContent = text;
        toast.style.position = "absolute";
        toast.style.top = "8px";
        toast.style.left = "50%";
        toast.style.transform = "translateX(-50%)";
        toast.style.zIndex = "40";
        toast.style.padding = "5px 11px";
        toast.style.borderRadius = "7px";
        toast.style.font = "11px ui-monospace, Menlo, monospace";
        toast.style.color = "rgba(255, 255, 255, 0.92)";
        toast.style.background = "rgba(18, 20, 26, 0.92)";
        toast.style.border = "1px solid rgba(255, 255, 255, 0.16)";
        toast.style.boxShadow = "0 4px 16px rgba(0, 0, 0, 0.45)";
        toast.style.pointerEvents = "none";
        toast.style.opacity = "0";
        toast.style.transition = "opacity 160ms ease";
        root.appendChild(toast);
        requestAnimationFrame(() => { toast.style.opacity = "1"; });
        costToast = toast;
        costToastTimer = setTimeout(() => {
            toast.style.opacity = "0";
            setTimeout(() => {
                if (toast === costToast) { toast.remove(); costToast = null; }
            }, 220);
        }, 2600);
    }

    function recordScanCost(cost) {
        state.scanCost = cost || null;
        if (cost && typeof cost.usd === "number") {
            state.scanSessionUsd += cost.usd;
        }
        showCostToast(costLine(cost));
    }

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
        // A scan augments the canvas: existing regions (including hand-drawn
        // ones) are kept and the scanned set is appended in front of them, so a
        // scan fills in around manual work instead of discarding it. Selection
        // is cleared so dragging a scanned region doesn't drag a previously
        // selected one. One syncWidget keeps the merge a single undo step.
        // Overlaps with existing regions are left for the user to resolve.
        state.boxes = state.boxes.concat(added);
        state.selection = new Set();
        state.primary = null;
        E.syncWidget();
    }

    async function onScanClick() {
        // A click while a scan is in flight cancels it (the busy cursor is the
        // affordance); the abort resolves as {aborted} below and exits quietly.
        if (state.scanning) {
            state.scanAbort?.abort();
            return;
        }
        const model = node.properties?.erpkScanModel;
        const img = upstreamImage(node, "image");
        if (!img || !img.complete || !img.naturalWidth) {
            state.scanError = "No loaded image to scan";
            E.render();
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
            E.render();
            return;
        }
        state.scanError = null;
        state.scanning = true;
        state.scanAbort = new AbortController();
        E.scanFxLoop();
        try {
            const body = { image: dataUrl, max_objects: SCAN_MAX_OBJECTS, engine: "gemini" };
            if (model) body.model = model;
            const segmenter = node.properties?.erpkSegmenter;
            if (segmenter) body.segmenter = segmenter;
            const res = await postScanWithTimeout(body, state.scanAbort);
            if (res.aborted) return;  // user cancel or node teardown: stay silent
            if (res.timedOut) {
                state.scanError = "Scan timed out";
            } else if (!res.ok || res.json.error) {
                state.scanError = res.json.error || `Scan failed (${res.status})`;
            } else {
                applyScanResults(res.json.objects);
                recordScanCost(res.json.cost);
            }
        } catch (err) {
            state.scanError = `Scan failed: ${err.message}`;
        } finally {
            state.scanning = false;
            state.scanAbort = null;
            E.render();
        }
    }

    function onHideToggle() {
        state.hideBoxes = !state.hideBoxes;
        E.render();
    }

    function onMaskToggle() {
        if (!state.boxes.some((b) => b.mask)) return;
        state.showMasks = !state.showMasks;
        E.render();
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
        E.closePanel();
        helpPanel = document.createElement("div");
        popoverZoom(helpPanel, "top right");
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
            ["Alt+drop a list row", "group under that region (again to ungroup)"],
            ["drag a region", "move selection"],
            ["Alt+click", "cycle overlapping regions"],
            ["double-click", "edit description in the inspector"],
            ["right-click", "region details, list, and depth order"],
            ["Del / Backspace", "delete selected"],
            ["Shift+Del", "cut out — remove & make transparent"],
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
        helpPanel.addEventListener("pointerdown", E.onPanelPointerDown);

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
    let scanSegmenters = null;    // {segmenters:[...], default:"..."} cached after a good fetch
    let scanSegmenterSelect = null;

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
        scanSegmenterSelect = null;
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
        const data = await fetchScanModels();
        if (data) scanModels = data;
        populateScanModels();
    }

    function populateScanSegmenters() {
        if (!scanSegmenterSelect) return;
        scanSegmenterSelect.textContent = "";
        const list = scanSegmenters && scanSegmenters.segmenters;
        if (!list || !list.length) {
            // No server-side segmenter list (transformers absent or fetch failed):
            // a value-less default so the scan omits "segmenter" and vit-base runs.
            const opt = document.createElement("option");
            opt.value = "";
            opt.textContent = "default (SAM ViT-Base)";
            opt.selected = true;
            scanSegmenterSelect.appendChild(opt);
            return;
        }
        const chosen = node.properties?.erpkSegmenter || scanSegmenters.default || list[0].id;
        for (const s of list) {
            const opt = document.createElement("option");
            opt.value = s.id;
            // A trailing ↓ marks weights that download on first use.
            opt.textContent = s.label + (s.downloaded ? "" : " ↓");
            if (s.id === chosen) opt.selected = true;
            scanSegmenterSelect.appendChild(opt);
        }
    }

    async function loadScanSegmenters() {
        if (scanSegmenters) { populateScanSegmenters(); return; }
        const data = await fetchScanSegmenters();
        if (data) scanSegmenters = data;
        populateScanSegmenters();
    }

    function openOptions() {
        E.closePanel();
        closeHelp();
        optionsPanel = document.createElement("div");
        popoverZoom(optionsPanel, "top right");
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
        header.textContent = "Options";
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

        const segLabel = document.createElement("div");
        segLabel.textContent = "Segmenter (masks)";
        segLabel.style.font = "9px 'Segoe UI', sans-serif";
        segLabel.style.color = "rgba(255, 255, 255, 0.7)";
        segLabel.style.padding = "7px 4px 3px";
        optionsPanel.appendChild(segLabel);

        scanSegmenterSelect = document.createElement("select");
        styleInput(scanSegmenterSelect);
        scanSegmenterSelect.style.fontSize = "11px";
        scanSegmenterSelect.addEventListener("change", () => {
            if (!node.properties) node.properties = {};
            if (scanSegmenterSelect.value) {
                node.properties.erpkSegmenter = scanSegmenterSelect.value;
            } else {
                delete node.properties.erpkSegmenter;
            }
        });
        optionsPanel.appendChild(scanSegmenterSelect);

        const hint = document.createElement("div");
        hint.textContent = "Gemini detects the regions; the segmenter builds the "
            + "masks (ViT-Base is fastest). ↓ downloads on first use.";
        hint.style.font = "8px 'Segoe UI', sans-serif";
        hint.style.color = "rgba(255, 255, 255, 0.4)";
        hint.style.padding = "5px 4px 1px";
        optionsPanel.appendChild(hint);

        // Removal fill: how cleared cut-out / move-origin areas are filled. These
        // drive the hidden removal_fill / chroma_color node widgets that execute
        // reads, so the setting lives here instead of cluttering the node body.
        const fillWidget = findWidget(node, "removal_fill");
        const colorWidget = findWidget(node, "chroma_color");

        const fillLabel = document.createElement("div");
        fillLabel.textContent = "Removal fill";
        fillLabel.style.font = "9px 'Segoe UI', sans-serif";
        fillLabel.style.color = "rgba(255, 255, 255, 0.7)";
        fillLabel.style.padding = "9px 4px 3px";
        fillLabel.style.borderTop = "1px solid " + HAIRLINE;
        fillLabel.style.marginTop = "6px";
        optionsPanel.appendChild(fillLabel);

        const fillSelect = document.createElement("select");
        styleInput(fillSelect);
        fillSelect.style.fontSize = "11px";
        for (const [val, text] of [["inpaint", "Inpaint (rebuild background)"],
                                   ["chroma", "Chroma key (flat color)"]]) {
            const opt = document.createElement("option");
            opt.value = val;
            opt.textContent = text;
            fillSelect.appendChild(opt);
        }
        fillSelect.value = fillWidget?.value === "chroma" ? "chroma" : "inpaint";
        optionsPanel.appendChild(fillSelect);

        const colorRow = document.createElement("div");
        colorRow.style.display = "flex";
        colorRow.style.alignItems = "center";
        colorRow.style.gap = "6px";
        colorRow.style.padding = "6px 4px 1px";
        const colorLabel = document.createElement("span");
        colorLabel.textContent = "Chroma color";
        colorLabel.style.font = "9px 'Segoe UI', sans-serif";
        colorLabel.style.color = "rgba(255, 255, 255, 0.7)";
        colorLabel.style.flex = "1 1 auto";
        const colorInput = document.createElement("input");
        colorInput.type = "color";
        colorInput.value = /^#[0-9a-fA-F]{6}$/.test(colorWidget?.value)
            ? colorWidget.value : "#00B140";
        colorInput.style.flex = "0 0 auto";
        colorInput.style.width = "30px";
        colorInput.style.height = "20px";
        colorInput.style.padding = "0";
        colorInput.style.border = "1px solid " + HAIRLINE;
        colorInput.style.borderRadius = "3px";
        colorInput.style.background = "transparent";
        colorInput.style.cursor = "pointer";
        colorRow.appendChild(colorLabel);
        colorRow.appendChild(colorInput);
        optionsPanel.appendChild(colorRow);

        const syncColorRow = () => {
            colorRow.style.display = fillSelect.value === "chroma" ? "flex" : "none";
        };
        syncColorRow();
        fillSelect.addEventListener("change", () => {
            if (fillWidget) fillWidget.value = fillSelect.value;
            syncColorRow();
        });
        colorInput.addEventListener("input", () => {
            if (colorWidget) colorWidget.value = colorInput.value;
        });

        optionsPanel.addEventListener("pointerdown", E.onPanelPointerDown);

        root.appendChild(optionsPanel);
        optionsPanel.style.right = "6px";
        optionsPanel.style.bottom = (root.offsetHeight - status.offsetTop + 4) + "px";

        loadScanModels();
        loadScanSegmenters();

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

    // screen mode renders the tip in the viewport (fixed, on document.body) for
    // the right-click panel, which is itself portaled out of root; otherwise the
    // tip is a root child in the editor's own coordinate space.
    function makeTipEl(text, controls, screen) {
        const el = document.createElement("div");
        el.style.position = screen ? "fixed" : "absolute";
        el.style.zIndex = screen ? "10001" : "30";
        el.style.maxWidth = "240px";
        el.style.padding = "3px 7px";
        el.style.background = PANEL_BG;
        el.style.border = "1px solid " + HAIRLINE;
        el.style.borderRadius = "4px";
        el.style.boxShadow = "0 4px 14px rgba(0, 0, 0, 0.45)";
        el.style.font = "9px 'Segoe UI', sans-serif";
        el.style.lineHeight = "1.5";
        el.style.color = "rgba(255, 255, 255, 0.85)";
        el.style.pointerEvents = "none";

        const body = document.createElement("div");
        body.textContent = text;
        body.style.whiteSpace = "pre-line";
        el.appendChild(body);

        // Controls sit below a hairline separator in a dimmer color, so they
        // read as metadata rather than part of the region's prompt.
        if (controls) {
            const ctl = document.createElement("div");
            ctl.textContent = controls;
            ctl.style.whiteSpace = "pre-line";
            ctl.style.marginTop = "4px";
            ctl.style.paddingTop = "4px";
            ctl.style.borderTop = "1px solid " + HAIRLINE;
            ctl.style.color = "rgba(255, 255, 255, 0.42)";
            el.appendChild(ctl);
        }

        (screen ? document.body : root).appendChild(el);
        return el;
    }

    function showTip(target) {
        const text = target.dataset.tip;
        if (!text) return;
        // The right-click panel is portaled to document.body and fixed in the
        // viewport, so its tips render in screen space, anchored to the target's
        // viewport rect, instead of the editor's graph-transformed coordinates.
        if (E.panel && E.panel.contains(target)) {
            tipEl = makeTipEl(text, null, true);
            const t = target.getBoundingClientRect();
            const maxX = window.innerWidth - tipEl.offsetWidth - 4;
            const left = t.left + t.width / 2 - tipEl.offsetWidth / 2;
            tipEl.style.left = Math.round(clamp(left, 4, Math.max(maxX, 4))) + "px";
            let top = t.top - tipEl.offsetHeight - 5;
            if (top < 4) top = t.bottom + 5;
            tipEl.style.top = Math.round(top) + "px";
            return;
        }
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
        // The controls line — chiefly so the buttonless ⇧+Del is discoverable.
        tipEl = makeTipEl(text,
            "drag move · Del delete · ⇧+Del cut out · right-click details");
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
        if (E.descWiredFor(box)) lines.push(`⌁ description wired from desc_${index + 1}`);
        if (E.refWiredFor(box)) lines.push(`▣ reference image from ref_${index + 1}`);
        return lines.join("\n");
    }

    function trackRegionTip(e) {
        const hit = E.maskAwareHit(E.pointerNorm(e));
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
            E.render();
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
        fsBtn.innerHTML = on ? MINIMIZE_SVG : MAXIMIZE_SVG;
        fsBtn.dataset.tip = on
            ? "Restore the editor to the node (F · Esc to exit)"
            : "Expand the editor to fill the window (F · Esc to exit)";
    }

    // In the node, ComfyUI's graph zoom magnifies the editor's fixed pixel
    // sizes; the fullscreen overlay escapes that transform, so popovers
    // compensate or they read tiny beside a wall-sized canvas.
    function popoverScale() {
        return root._erpkExpanded ? 1.45 : 1;
    }

    // transform, not CSS zoom: zoom multiplies the element's own left/top so
    // positioned popovers land at the wrong place; a scale transform keeps
    // positioning in parent pixels (only clamp math sees the factor).
    function popoverZoom(el, origin = "top left") {
        const z = popoverScale();
        el.style.transformOrigin = origin;
        el.style.transform = z !== 1 ? `scale(${z})` : "";
    }

    // ComfyUI's undo keybinding listens in the capture phase at the
    // document, ahead of any editor handler — letting it through both
    // double-undoes (workflow + regions) and re-configures the node, which
    // flashes the widget and tears down fullscreen. Window capture runs
    // first, so the editor can own Ctrl/Cmd+Z for events born inside it.
    function onGlobalUndoKey(e) {
        if (!(e.ctrlKey || e.metaKey) || e.key.toLowerCase() !== "z") return;
        const target = e.target;
        if (!(target instanceof HTMLElement) || !root.contains(target)) return;
        const editable = target.tagName === "INPUT"
            || target.tagName === "TEXTAREA" || target.isContentEditable;
        e.stopPropagation();
        if (editable) return;  // native text-field undo, ComfyUI kept out
        e.preventDefault();
        if (e.shiftKey) E.redoRegions();
        else E.undoRegions();
    }

    // Capture phase so it sees Escape regardless of focus. Each Escape goes
    // to one consumer: an open popover, then a focused text field (blur), and
    // only then the overlay itself.
    function onFsDocKeyDown(e) {
        if (e.key !== "Escape" || !root._erpkExpanded) return;
        if (e._erpkEscapeClosedPopover || helpPanel || E.panel) return;
        const field = document.activeElement;
        if (field instanceof HTMLElement && root.contains(field)
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
        requestAnimationFrame(() => E.layout());
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
        requestAnimationFrame(() => E.layout());
    }

    function onToggleFullscreen() {
        if (root._erpkExpanded) collapse();
        else expand();
    }

    Object.assign(E, {
        restoreGridPrefs,
        onGridToggle,
        onGridSizeInput,
        onGridSizeBlur,
        onGridColorInput,
        onGridAlphaInput,
        onGridAlphaBlur,
        onGridSizeKeyDown,
        onSnapToggle,
        disarmClear,
        onClearClick,
        onSendBack,
        onBringForward,
        onMatchClick,
        recordScanCost,
        onScanClick,
        onHideToggle,
        onMaskToggle,
        onHelpToggle,
        closeHelp,
        onOptionsToggle,
        closeOptions,
        hideTip,
        trackRegionTip,
        onCanvasTipLeave,
        onTipOver,
        onTipOut,
        popoverScale,
        popoverZoom,
        onGlobalUndoKey,
        onToggleFullscreen,
        collapse,
    });
}
