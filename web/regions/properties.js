// ABOUTME: The right-click region detail panel — thumbnail, name, geometry, prompt, kind, sockets, scan.
// ABOUTME: Builds and refreshes the inspector for the primary region; mutations flow through the injected E.
// @ts-check

import { clamp, colorForRegion, hexToRgba } from "./geometry.js";
import { frameDims, upstreamImage } from "./node_access.js";
import { maskAlphaCanvas } from "./masks.js";
import { postScanWithTimeout } from "./scanClient.js";
import { makeStripButton, styleInput, setEyeIcon } from "./styles.js";
import {
    MIN_REGION_SIZE,
    SCAN_MAX_EDGE_PX,
    SCAN_MAX_OBJECTS,
    ACTIVE_GREEN,
    ACTIVE_GREEN_BORDER,
    HAIRLINE,
    PANEL_INPUT_BG,
    TRASH_SVG,
    IMAGE_SVG,
    SPARKLES_SVG,
    LINK_SVG,
    DANGER_RED_DIM,
    DANGER_RED_BORDER,
} from "./constants.js";

export function installProperties(E) {
    const { node, state } = E;

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
        E.syncWidget();
        E.render();
    }

    function refreshPanelDim() {
        if (!E.panelDimFields) return;
        const box = state.primary;
        const dims = frameDims(node);
        const px = box ? {
            x: Math.round(box.x * dims.w),
            y: Math.round(box.y * dims.h),
            w: Math.round(box.w * dims.w),
            h: Math.round(box.h * dims.h),
        } : null;
        for (const key of Object.keys(E.panelDimFields)) {
            const input = E.panelDimFields[key];
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
        E.syncWidget();
        E.render();
    }

    // The prompt textarea edits region.desc, the text that feeds generation.
    function applyPanelDesc(input) {
        const box = state.primary;
        if (!box) return;
        box.desc = input.value;
        E.syncWidget();
        E.render();
    }

    function applyPanelText(input) {
        const box = state.primary;
        if (!box) return;
        box.text = input.value;
        E.syncWidget();
        E.render();
    }

    function onPanelKindChange(kind) {
        const box = state.primary;
        if (!box) return;
        box.kind = kind === "text" ? "text" : "object";
        E.syncWidget();
        E.render();
        refreshPanelDetail();
    }

    // Detect objects inside one region: the crop scans like a tiny image and
    // the results map back through the host box into frame space. Findings
    // append; the host region is left for the user to keep or delete.
    async function onSectionScan(host) {
        // A re-trigger while a scan is in flight cancels it instead of stacking.
        if (state.scanning) {
            state.scanAbort?.abort();
            return;
        }
        if (!host) return;
        const img = upstreamImage(node, "image");
        if (!img || !img.complete || !img.naturalWidth) {
            state.scanError = "No loaded image to scan";
            E.render();
            return;
        }
        const frame = { x: host.x, y: host.y, w: host.w, h: host.h };
        const sw = Math.max(1, Math.round(frame.w * img.naturalWidth));
        const sh = Math.max(1, Math.round(frame.h * img.naturalHeight));
        let dataUrl;
        try {
            const scale = Math.min(1, SCAN_MAX_EDGE_PX / Math.max(sw, sh));
            const off = document.createElement("canvas");
            off.width = Math.max(1, Math.round(sw * scale));
            off.height = Math.max(1, Math.round(sh * scale));
            const offCtx = off.getContext("2d");
            offCtx.fillStyle = "#fff";
            offCtx.fillRect(0, 0, off.width, off.height);
            offCtx.drawImage(
                img,
                frame.x * img.naturalWidth, frame.y * img.naturalHeight,
                sw, sh, 0, 0, off.width, off.height,
            );
            dataUrl = off.toDataURL("image/jpeg", 0.85);
        } catch (err) {
            state.scanError = "Can't read image (cross-origin?)";
            E.render();
            return;
        }
        state.scanError = null;
        state.scanning = true;
        state.scanBounds = frame;
        state.scanAbort = new AbortController();
        E.scanFxLoop();
        try {
            const model = node.properties?.erpkScanModel;
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
                applySectionResults(res.json.objects, frame, host);
                E.recordScanCost(res.json.cost);
            }
        } catch (err) {
            state.scanError = `Scan failed: ${err.message}`;
        } finally {
            state.scanning = false;
            state.scanBounds = null;
            state.scanAbort = null;
            E.render();
        }
    }

    // Maps crop-space scan objects back into frame space and REPLACES the
    // host region with them at its depth slot — the host was the rough
    // draft, the detections are its refinement.
    function applySectionResults(objects, frame, host) {
        const sorted = (Array.isArray(objects) ? objects.slice() : [])
            .sort((a, b) => (Number(a?.depth_rank) || 0) - (Number(b?.depth_rank) || 0));
        const added = [];
        for (const obj of sorted) {
            const src = obj?.box;
            if (!src || typeof src !== "object") continue;
            const nums = [src.x, src.y, src.w, src.h].map((v) => Number(v ?? 0));
            if (!nums.every(Number.isFinite)) continue;
            const x = clamp(frame.x + nums[0] * frame.w, 0, 1);
            const y = clamp(frame.y + nums[1] * frame.h, 0, 1);
            const w = clamp(nums[2] * frame.w, 0, 1 - x);
            const h = clamp(nums[3] * frame.h, 0, 1 - y);
            if (w <= 0.005 || h <= 0.005) continue;
            const region = {
                x, y, w, h,
                kind: "object",
                desc: (typeof obj.caption === "string" && obj.caption)
                    || (typeof obj.name === "string" ? obj.name : ""),
                text: "",
            };
            if (typeof obj.name === "string" && obj.name) region.group = obj.name;
            if (typeof obj.mask === "string" && obj.mask) region.mask = obj.mask;
            region.src = { x, y, w, h };
            added.push(region);
        }
        if (!added.length) {
            state.scanError = "Scan found no objects in the region";
            return;
        }
        const slot = state.boxes.indexOf(host);
        if (added.length === 1 && slot >= 0) {
            // A lone detection is the host, refined — merging in place keeps
            // the host's identity (id, parent, wired sockets) instead of
            // wrapping one region in a pointless group.
            const r = added[0];
            for (const key of ["_erpkMaskImg", "_erpkMaskData",
                               "_erpkCutout", "_erpkGhostChecker"]) {
                delete host[key];
            }
            host.x = r.x; host.y = r.y; host.w = r.w; host.h = r.h;
            host.kind = "object";
            host.desc = r.desc;
            host.group = r.group || host.group;
            if (r.mask) host.mask = r.mask; else delete host.mask;
            host.src = r.src;
            E.select(host);
        } else if (slot >= 0) {
            // The host stays and becomes the group parent; the detections
            // nest under it as children, directly in front in z-order. An
            // unnamed host borrows its largest child's name.
            if (!host.group) {
                const biggest = added.reduce(
                    (a, b) => (b.w * b.h > a.w * a.h ? b : a));
                host.group = biggest.group ? biggest.group + " group" : "group";
            }
            for (const region of added) region.parent = E.regionId(host);
            state.boxes.splice(slot + 1, 0, ...added);
            E.select(added[0]);
        } else {
            state.boxes.push(...added);
            E.select(added[0]);
        }
        E.syncWidget();
    }

    // Tinted mask silhouette in the detail thumbnail, or a flat color wash when
    // the region carries no mask.
    function drawPanelThumb(box) {
        if (!E.panelThumb) return;
        const tctx = E.panelThumb.getContext("2d");
        const w = E.panelThumb.width;
        const h = E.panelThumb.height;
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
                const alpha = maskAlphaCanvas(box);
                tctx.fillStyle = color;
                tctx.fillRect(0, 0, w, h);
                if (alpha) {
                    tctx.globalCompositeOperation = "destination-in";
                    tctx.drawImage(alpha, 0, 0, w, h);
                    tctx.globalCompositeOperation = "source-over";
                }
                return;
            }
            m.addEventListener("load", () => {
                if (E.panelThumb && state.primary === box) drawPanelThumb(box);
            }, { once: true });
        }
        tctx.fillStyle = hexToRgba(color, 0.28);
        tctx.fillRect(0, 0, w, h);
    }

    function refreshPanelDetail() {
        const box = state.primary;
        // The detail is the inspector for the selected region; with no selection
        // (an empty-canvas right-click) the panel shows just the list. Selecting
        // any row — including a cut-out, which has no clickable canvas face —
        // reveals it. Built unconditionally on open, shown only when something is
        // selected.
        if (E.panelDetail) E.panelDetail.style.display = box ? "flex" : "none";
        if (E.panelNameInput && document.activeElement !== E.panelNameInput) {
            E.panelNameInput.value = box ? (box.group || "") : "";
        }
        if (E.panelDescInput && document.activeElement !== E.panelDescInput) {
            E.panelDescInput.value = box ? (box.desc || "") : "";
        }
        if (E.panelEyeBtn) {
            const hidden = !!(box && box.hidden);
            setEyeIcon(E.panelEyeBtn, hidden);
            E.panelEyeBtn.dataset.tip = hidden ? "Show region" : "Hide region";
        }
        if (E.panelKindBtns) {
            const kind = box?.kind === "text" ? "text" : "object";
            for (const [value, btn] of Object.entries(E.panelKindBtns)) {
                const on = value === kind;
                btn.classList.toggle("erpk-btn-active", on);
                btn.style.color = on ? ACTIVE_GREEN : "rgba(255, 255, 255, 0.65)";
                btn.style.borderColor = on
                    ? ACTIVE_GREEN_BORDER : "rgba(255, 255, 255, 0.14)";
            }
        }
        if (E.panelTextInput) {
            const showText = box?.kind === "text";
            const appearing = showText && E.panelTextInput.style.display === "none";
            E.panelTextInput.style.display = showText ? "" : "none";
            if (E.panelTextLabel) E.panelTextLabel.style.display = showText ? "" : "none";
            if (appearing) {
                E.panelTextInput.style.opacity = "0";
                requestAnimationFrame(() => { E.panelTextInput.style.opacity = "1"; });
            }
            if (showText && document.activeElement !== E.panelTextInput) {
                E.panelTextInput.value = box.text || "";
            }
        }
        if (E.panelPlugBtn) E.syncSocketToggle(E.panelPlugBtn, "desc", box);
        if (E.panelRefBtn) E.syncSocketToggle(E.panelRefBtn, "ref", box);
        if (E.panelScanBtn) {
            const ready = !state.scanning && !!upstreamImage(node, "image");
            E.panelScanBtn.disabled = !ready;
            E.panelScanBtn.style.opacity = ready ? "1" : "0.45";
        }
        // A control only shows for regions it actually affects; a row that would
        // do nothing is hidden, not greyed. Applied by governs a move, a cut-out,
        // or a ref-wired addition (Node composites it, Model places it). A marker
        // is for an element the model places itself — an addition or a Model move.
        const moved = !!box && E.regionMoved(box);
        const refWired = !!box && E.refWiredFor(box);
        const cutout = box?.cutout === true;
        const editByApplies = !!box && (cutout || moved || refWired);
        const nodeRefInsert = refWired && box?.edit_by !== "model";
        const modelCutout = cutout && box?.edit_by === "model";
        const markerApplies = !!box && !nodeRefInsert && (
            modelCutout
            || (!cutout && (moved ? box.edit_by === "model" : box.src == null)));
        if (E.panelEditByRow) E.panelEditByRow.style.display = editByApplies ? "flex" : "none";
        if (E.panelMarkersRow) E.panelMarkersRow.style.display = markerApplies ? "flex" : "none";
        if (E.panelEditByBtns) {
            const mode = box?.edit_by === "model" ? "model" : "node";
            for (const [value, btn] of Object.entries(E.panelEditByBtns)) {
                const on = value === mode;
                btn.classList.toggle("erpk-btn-active", on);
                btn.style.color = on ? ACTIVE_GREEN : "rgba(255, 255, 255, 0.65)";
                btn.style.borderColor = on
                    ? ACTIVE_GREEN_BORDER : "rgba(255, 255, 255, 0.14)";
                btn.dataset.tip = value === "node"
                    ? "Apply this move/cut-out/insertion in the node: deterministic, "
                      + "exact size and position (best for precise placement)"
                    : "Apply it with the edit model: it places and relights, but "
                      + "size/position drift (less precise)";
            }
        }
        if (E.panelMarkersBtns) {
            const on = box?.markers !== false;
            for (const [value, btn] of Object.entries(E.panelMarkersBtns)) {
                const active = (value === "on") === on;
                btn.classList.toggle("erpk-btn-active", active);
                btn.style.color = active ? ACTIVE_GREEN : "rgba(255, 255, 255, 0.65)";
                btn.style.borderColor = active
                    ? ACTIVE_GREEN_BORDER : "rgba(255, 255, 255, 0.14)";
                btn.dataset.tip = value === "on"
                    ? "Draw a colored placement dot for this element; the prompt "
                      + "asks the model to center it there and paint the dot out"
                    : "No placement dot for this element";
            }
        }
        drawPanelThumb(box);
    }

    // Builds the detail section above the region list and appends it to the
    // panel. Right-clicking a region shows its detail: a mask thumbnail, the
    // layer name, the X/Y/W/H pixel fields, the prompt, and hide / delete
    // actions. Empty-canvas right-clicks open just the list (no detail).
    function buildDetail(panel) {
        // The detail is the inspector for the selected region: lift it one
        // elevation step above the list (a faint tint + card border) so the
        // "editing this one" surface reads as distinct from the layer stack.
        const detail = document.createElement("div");
        detail.style.display = "flex";
        detail.style.flexDirection = "column";
        detail.style.gap = "6px";
        detail.style.padding = "8px";
        detail.style.marginBottom = "7px";
        detail.style.background = "rgba(255, 255, 255, 0.03)";
        detail.style.border = "1px solid " + HAIRLINE;
        detail.style.borderRadius = "6px";

        // One control metric across the detail: 10px type, 2px/6px pads.
        const microLabel = (text) => {
            const el = document.createElement("span");
            el.textContent = text;
            el.style.font = "9px 'Segoe UI', sans-serif";
            el.style.letterSpacing = "0.6px";
            el.style.textTransform = "uppercase";
            el.style.color = "rgba(255, 255, 255, 0.45)";
            el.style.marginBottom = "-3px";
            return el;
        };

        // Every chip in the card shares one metric — same height, padding, radius,
        // and type — so the controls read as a single uniform set, not a jumble.
        const chip = (btn) => {
            btn.style.font = "10px 'Segoe UI', sans-serif";
            btn.style.lineHeight = "1";
            btn.style.height = "24px";
            btn.style.boxSizing = "border-box";
            btn.style.padding = "0 9px";
            btn.style.borderRadius = "5px";
            btn.style.display = "inline-flex";
            btn.style.alignItems = "center";
            btn.style.justifyContent = "center";
            btn.style.gap = "4px";
            return btn;
        };

        // A uniform chip with a leading Lucide icon and a text label, so the
        // footer verbs match the toolbar's icon family instead of bare glyphs.
        const iconChip = (svg, text) => {
            const btn = chip(makeStripButton(""));
            btn.innerHTML = svg;
            const lbl = document.createElement("span");
            lbl.textContent = text;
            btn.appendChild(lbl);
            return btn;
        };

        // A small uppercase inline tag that introduces a control group. A fixed
        // min-width keeps stacked rows' controls (Applied by, Marker) aligned on a
        // common left edge regardless of label length.
        const groupTag = (text) => {
            const el = document.createElement("span");
            el.textContent = text;
            el.style.font = "9px 'Segoe UI', sans-serif";
            el.style.letterSpacing = "0.6px";
            el.style.textTransform = "uppercase";
            el.style.color = "rgba(255, 255, 255, 0.4)";
            el.style.flex = "0 0 auto";
            el.style.minWidth = "64px";
            return el;
        };

        // Identity line: what the region IS — swatch-scale thumb, name,
        // and the kind segmented control (cause above its effect).
        const topRow = document.createElement("div");
        topRow.style.display = "flex";
        topRow.style.alignItems = "center";
        topRow.style.gap = "6px";

        const panelThumb = document.createElement("canvas");
        panelThumb.width = 24;
        panelThumb.height = 24;
        panelThumb.style.flex = "0 0 auto";
        panelThumb.style.width = "24px";
        panelThumb.style.height = "24px";
        panelThumb.style.boxSizing = "border-box";
        panelThumb.style.borderRadius = "5px";
        panelThumb.style.border = "1px solid " + HAIRLINE;
        panelThumb.style.background = PANEL_INPUT_BG;

        const panelNameInput = document.createElement("input");
        panelNameInput.type = "text";
        panelNameInput.placeholder = "name";
        panelNameInput.dataset.tip = "Layer name — same-named regions share a color";
        styleInput(panelNameInput);
        panelNameInput.style.width = "";
        panelNameInput.style.flex = "1 1 auto";
        panelNameInput.style.minWidth = "0";
        panelNameInput.style.fontSize = "10px";
        panelNameInput.style.height = "24px";
        panelNameInput.style.padding = "0 8px";
        panelNameInput.style.borderRadius = "5px";
        panelNameInput.addEventListener("input", () => applyPanelName(panelNameInput));

        const panelKindBtns = {};
        const kindGroup = document.createElement("div");
        kindGroup.style.display = "flex";
        kindGroup.style.flex = "0 0 auto";
        kindGroup.style.gap = "2px";
        for (const kind of ["object", "text"]) {
            const btn = chip(makeStripButton(kind === "object" ? "Object" : "Text"));
            btn.dataset.tip = kind === "text"
                ? "Render literal text in this region"
                : "An object in the scene";
            btn.addEventListener("click", (e) => {
                e.stopPropagation();
                onPanelKindChange(kind);
            });
            panelKindBtns[kind] = btn;
            kindGroup.appendChild(btn);
        }

        const panelEyeBtn = chip(makeStripButton(""));
        setEyeIcon(panelEyeBtn, false);
        panelEyeBtn.style.flex = "0 0 auto";
        panelEyeBtn.style.padding = "0 7px";
        panelEyeBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            E.toggleRegionHidden(state.primary);
        });

        topRow.appendChild(panelEyeBtn);
        topRow.appendChild(panelThumb);
        topRow.appendChild(panelNameInput);
        topRow.appendChild(kindGroup);
        detail.appendChild(topRow);

        const dimRow = document.createElement("div");
        dimRow.style.display = "flex";
        dimRow.style.alignItems = "center";
        dimRow.style.gap = "4px";
        dimRow.style.font = "8px 'Segoe UI', sans-serif";
        dimRow.style.color = "rgba(255, 255, 255, 0.45)";
        const panelDimFields = {};
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
            input.style.padding = "2px 4px";
            input.style.fontSize = "10px";
            input.addEventListener("input", () => applyPanelDim(key, input));
            panelDimFields[key] = input;
            dimRow.appendChild(label);
            dimRow.appendChild(input);
        }
        detail.appendChild(dimRow);

        detail.appendChild(microLabel("prompt"));
        const panelDescInput = document.createElement("textarea");
        panelDescInput.rows = 2;
        panelDescInput.placeholder = "what should appear in this region";
        panelDescInput.dataset.tip = "Region prompt — feeds generation for this layer";
        styleInput(panelDescInput);
        panelDescInput.style.fontSize = "10px";
        panelDescInput.style.resize = "vertical";
        panelDescInput.style.minHeight = "30px";
        panelDescInput.addEventListener("input", () => applyPanelDesc(panelDescInput));
        detail.appendChild(panelDescInput);

        const panelTextLabel = microLabel("renders");
        detail.appendChild(panelTextLabel);
        const panelTextInput = document.createElement("input");
        panelTextInput.type = "text";
        panelTextInput.placeholder = "literal text to draw";
        panelTextInput.dataset.tip =
            "Literal text the model should render inside this region";
        styleInput(panelTextInput);
        panelTextInput.style.fontSize = "10px";
        panelTextInput.style.padding = "2px 6px";
        panelTextInput.style.transition = "opacity 0.12s ease-out";
        panelTextInput.addEventListener("input",
            () => applyPanelText(panelTextInput));
        detail.appendChild(panelTextInput);

        // "Applied by" group: who performs this region's move/cut-out. "Node" =
        // deterministic composite/inpaint (default, exact size/position); "Model"
        // = the edit model relocates and relights it. The group dims when the
        // region has no geometric edit, where the choice has no effect.
        const editByRow = document.createElement("div");
        editByRow.style.display = "flex";
        editByRow.style.alignItems = "center";
        editByRow.style.gap = "7px";
        editByRow.appendChild(groupTag("applied by"));
        const panelEditByBtns = {};
        const editByGroup = document.createElement("div");
        editByGroup.style.display = "flex";
        editByGroup.style.gap = "4px";
        for (const mode of ["node", "model"]) {
            const btn = chip(makeStripButton(mode === "node" ? "Node" : "Model"));
            btn.addEventListener("click", (e) => {
                e.stopPropagation();
                E.setRegionEditBy(state.primary, mode);
                refreshPanelDetail();
            });
            panelEditByBtns[mode] = btn;
            editByGroup.appendChild(btn);
        }
        editByRow.appendChild(editByGroup);
        detail.appendChild(editByRow);

        // "Marker" group: draw a colored placement dot the edit model can target
        // when it places this element itself (an addition or a Model move). On by
        // default; node-composited regions ignore it since their pixels are placed.
        const markersRow = document.createElement("div");
        markersRow.style.display = "flex";
        markersRow.style.alignItems = "center";
        markersRow.style.gap = "7px";
        markersRow.appendChild(groupTag("marker"));
        const panelMarkersBtns = {};
        const markersGroup = document.createElement("div");
        markersGroup.style.display = "flex";
        markersGroup.style.gap = "4px";
        for (const value of ["on", "off"]) {
            const btn = chip(makeStripButton(value === "on" ? "On" : "Off"));
            btn.addEventListener("click", (e) => {
                e.stopPropagation();
                E.setRegionMarkers(state.primary, value === "on");
                refreshPanelDetail();
            });
            panelMarkersBtns[value] = btn;
            markersGroup.appendChild(btn);
        }
        markersRow.appendChild(markersGroup);
        detail.appendChild(markersRow);

        // Action row: labeled augment chips on the left, the destructive delete
        // isolated on the right (far from the dismissal corner), neutral until
        // its own hover. Text labels replace the cryptic icons.
        const actions = document.createElement("div");
        actions.style.display = "flex";
        actions.style.alignItems = "center";
        actions.style.gap = "6px";
        // A hairline rule sets the action verbs apart from the applied-by group.
        actions.style.borderTop = "1px solid " + HAIRLINE;
        actions.style.paddingTop = "8px";
        actions.style.marginTop = "1px";

        const panelScanBtn = iconChip(SPARKLES_SVG, "Scan");
        panelScanBtn.dataset.tip = "Detect objects inside this region only";
        panelScanBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            onSectionScan(state.primary);
        });

        const panelPlugBtn = iconChip(LINK_SVG, "Desc");
        panelPlugBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            E.onPlugToggle();
            refreshPanelDetail();
        });

        const panelRefBtn = iconChip(IMAGE_SVG, "Ref");
        panelRefBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            E.onRefToggle();
            refreshPanelDetail();
        });

        const spacer = document.createElement("span");
        spacer.style.flex = "1 1 auto";

        // The one prominent delete (unlike the quiet per-row ones) stays red so
        // it always reads as destructive; a trash icon names the action.
        const detDelBtn = iconChip(TRASH_SVG, "Delete");
        detDelBtn.classList.add("erpk-btn-danger");
        detDelBtn.dataset.tip = "Delete region";
        detDelBtn.style.color = DANGER_RED_DIM;
        detDelBtn.style.borderColor = DANGER_RED_BORDER;
        detDelBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            E.deleteRegion(state.primary);
        });

        actions.appendChild(panelScanBtn);
        actions.appendChild(panelPlugBtn);
        actions.appendChild(panelRefBtn);
        actions.appendChild(spacer);
        actions.appendChild(detDelBtn);
        detail.appendChild(actions);

        // Keep presses and typing inside the detail from starting a row
        // drag or reaching the canvas and ComfyUI's global hotkeys.
        detail.addEventListener("pointerdown", (e) => e.stopPropagation());
        detail.addEventListener("keydown", (e) => e.stopPropagation());
        panel.appendChild(detail);

        // Publish the field references so refresh/redraw can reach them and
        // closePanel can drop them.
        E.panelDetail = detail;
        E.panelThumb = panelThumb;
        E.panelNameInput = panelNameInput;
        E.panelKindBtns = panelKindBtns;
        E.panelEyeBtn = panelEyeBtn;
        E.panelDimFields = panelDimFields;
        E.panelDescInput = panelDescInput;
        E.panelTextLabel = panelTextLabel;
        E.panelTextInput = panelTextInput;
        E.panelScanBtn = panelScanBtn;
        E.panelEditByRow = editByRow;
        E.panelEditByBtns = panelEditByBtns;
        E.panelMarkersRow = markersRow;
        E.panelMarkersBtns = panelMarkersBtns;
        E.panelPlugBtn = panelPlugBtn;
        E.panelRefBtn = panelRefBtn;
    }

    Object.assign(E, { refreshPanelDim, refreshPanelDetail, buildDetail });
}
