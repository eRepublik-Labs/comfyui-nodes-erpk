// ABOUTME: The right-click region list panel — rows front-to-back with select, duplicate, delete, drag-reorder.
// ABOUTME: Hosts the detail section (built by properties) and groups; mutations flow through the injected E.
// @ts-check

import { clamp, regionColor } from "./geometry.js";
import { makeStripButton, setEyeIcon, labelControlsFromTips } from "./styles.js";
import {
    HAIRLINE,
    PANEL_BG,
    ACTIVE_GREEN,
    COPY_SVG,
    TRASH_SVG,
} from "./constants.js";

export function installLayers(E) {
    const { state, root, canvas } = E;

    let panelList = null;

    function closePanel() {
        if (!E.panel) return;
        E.hideTip();  // a tip hovering a panel control would otherwise orphan
        document.removeEventListener("pointerdown", onDocPointerDown, true);
        document.removeEventListener("keydown", onDocKeyDown, true);
        E.panel.remove();
        E.panel = null;
        panelList = null;
        E.panelDetail = null;
        E.panelDimFields = null;
        E.panelNameInput = null;
        E.panelDescInput = null;
        E.panelEyeBtn = null;
        E.panelThumb = null;
        E.panelKindBtns = null;
        E.panelTextLabel = null;
        E.panelTextInput = null;
        E.panelPlugBtn = null;
        E.panelRefBtn = null;
        E.panelScanBtn = null;
        E.panelEditByBtns = null;
    }

    function onDocPointerDown(e) {
        if (!E.panel || E.panel.contains(e.target)) return;
        // Right-button presses on the canvas resolve through the contextmenu
        // toggle instead, so one gesture doesn't close and then reopen.
        if (e.button === 2 && e.target === canvas) return;
        closePanel();
    }

    function onDocKeyDown(e) {
        if (e.key === "Escape" && E.panel) {
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
        E.pasteRegions([box]);
        renderPanelRows();
    }

    function deleteRegion(box) {
        const index = state.boxes.indexOf(box);
        if (index < 0) return;
        for (const child of E.childrenOf(box)) {
            if (box.parent) child.parent = box.parent;
            else delete child.parent;
        }
        state.boxes.splice(index, 1);
        state.selection.delete(box);
        if (state.primary === box) state.primary = E.lastSelected();
        E.syncWidget();
        E.render();
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
        // Collapsed descendants have no rows; reinsert each after its parent
        // so the full z-array survives a reorder around folded groups.
        const missing = state.boxes.filter((b) => !order.includes(b));
        for (const m of missing) {
            const p = E.parentRegionOf(m);
            let idx = p ? order.indexOf(p) : -1;
            if (idx === -1) { order.push(m); continue; }
            while (idx + 1 < order.length && E.isDescendantOf(order[idx + 1], p)) {
                idx++;
            }
            order.splice(idx + 1, 0, m);
        }
        // A keyboard mutation mid-drag invalidates the row snapshot; refuse a
        // reorder that would add or drop regions and just rebuild the list.
        const valid = order.length === state.boxes.length
            && order.every((box) => state.boxes.includes(box));
        if (valid) {
            state.boxes = E.normalizeGroups(order);
            E.syncWidget();
        }
        E.render();
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
        E.panelRowDragging = true;
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

        function onRowUp(ev) {
            window.removeEventListener("pointermove", onRowMove, true);
            window.removeEventListener("pointerup", onRowUp, true);
            window.removeEventListener("pointercancel", onRowUp, true);
            E.panelRowDragging = false;
            for (const el of rows) {
                el.style.transition = "";
                el.style.transform = "";
            }
            row.style.opacity = "";
            row.style.position = "";
            row.style.zIndex = "";
            if (dragging) {
                // Alt-drop nests the dragged region under the row it lands
                // on; Alt-dropping onto its current parent ungroups it.
                const dropBox = rows[targetIndex]?._erpkBox;
                const dragBox = row._erpkBox;
                if (ev?.altKey && dropBox && dropBox !== dragBox) {
                    if (E.parentRegionOf(dragBox) === dropBox) {
                        delete dragBox.parent;
                    } else if (!E.isDescendantOf(dropBox, dragBox)) {
                        dragBox.parent = E.regionId(dropBox);
                    }
                    state.boxes = E.normalizeGroups(state.boxes);
                    E.syncWidget();
                    E.render();
                    renderPanelRows();
                    return;
                }
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
                E.select(row._erpkBox);
                E.render();
                renderPanelRows();
            } else {
                renderPanelRows();
            }
        }

        window.addEventListener("pointermove", onRowMove, true);
        window.addEventListener("pointerup", onRowUp, true);
        window.addEventListener("pointercancel", onRowUp, true);
    }

    function buildPanelRow(box, depth = 0) {
        const index = state.boxes.indexOf(box);
        const row = document.createElement("div");
        (/** @type {any} */ (row))._erpkBox = box;
        row.className = "erpk-region-row";
        if (state.selection.has(box)) row.classList.add("erpk-region-row-selected");
        row.style.display = "flex";
        row.style.alignItems = "center";
        row.style.gap = "7px";
        row.style.padding = "4px 6px";
        row.style.paddingLeft = (6 + depth * 14) + "px";
        row.style.borderRadius = "4px";
        row.style.cursor = "grab";
        row.style.border = "1px solid transparent";
        row.style.font = "10px 'Segoe UI', sans-serif";
        row.style.color = "rgba(255, 255, 255, 0.82)";

        // The region's hue as a vertical spine — the one element that ties each
        // row to its box on the canvas. The list's only saturated color.
        const rail = document.createElement("span");
        rail.style.flex = "0 0 auto";
        rail.style.width = "3px";
        rail.style.height = "15px";
        rail.style.borderRadius = "2px";
        rail.style.background = regionColor(index);

        const num = document.createElement("span");
        num.style.flex = "0 0 auto";
        num.style.color = "rgba(255, 255, 255, 0.4)";
        num.style.fontVariantNumeric = "tabular-nums";
        num.textContent = String(index + 1).padStart(2, "0");

        const plug = document.createElement("span");
        plug.style.flex = "0 0 auto";
        plug.style.color = regionColor(index);
        plug.dataset.tip = "Description wired from a desc input";
        plug.textContent = "⌁";
        plug.style.display = E.descWiredFor(box) ? "" : "none";

        const refMark = document.createElement("span");
        refMark.style.flex = "0 0 auto";
        refMark.style.color = regionColor(index);
        refMark.dataset.tip = "Reference image wired from a ref input";
        refMark.textContent = "▣";
        refMark.style.display = E.refWiredFor(box) ? "" : "none";

        // Flags a region whose move/cut-out is applied by the model, not the node.
        const modelMark = document.createElement("span");
        modelMark.style.flex = "0 0 auto";
        modelMark.style.color = ACTIVE_GREEN;
        modelMark.dataset.tip = "Move/cut-out applied by the edit model, not the node";
        modelMark.textContent = "✦";
        modelMark.style.display = box.edit_by === "model" ? "" : "none";

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
        // A cut-out region reads struck through — it is out of the scene.
        if (box.cutout) {
            label.style.textDecoration = "line-through";
            label.style.color = "rgba(255, 255, 255, 0.45)";
            row.dataset.tip = "Cut out — select then ⇧Del to restore";
        }

        // The eye stays visible (visibility is the most-used row control) but
        // dimmed at rest via .erpk-row-eye; no inline opacity, or it would beat
        // the hover rule. Border dropped so it reads as a glyph, not a button.
        const eyeBtn = makeStripButton("");
        setEyeIcon(eyeBtn, E.effectiveHidden(box));
        eyeBtn.classList.add("erpk-row-eye");
        eyeBtn.style.border = "none";
        eyeBtn.dataset.tip = box.hidden ? "Show region" : "Hide region";
        eyeBtn.style.fontSize = "11px";
        eyeBtn.style.padding = "0 2px";

        // Duplicate and delete only appear on row hover (.erpk-row-tool) and are
        // borderless neutral glyphs; delete reddens only on its own hover, so the
        // list is not a wall of red ✕.
        const dupBtn = makeStripButton("");
        dupBtn.innerHTML = COPY_SVG;
        dupBtn.classList.add("erpk-row-tool");
        dupBtn.dataset.tip = "Duplicate region";
        dupBtn.style.border = "none";
        dupBtn.style.color = "rgba(255, 255, 255, 0.5)";
        dupBtn.style.padding = "0 3px";
        const delBtn = makeStripButton("");
        delBtn.innerHTML = TRASH_SVG;
        delBtn.classList.add("erpk-btn-danger", "erpk-row-tool");
        delBtn.dataset.tip = "Delete region";
        delBtn.style.border = "none";
        delBtn.style.color = "rgba(255, 255, 255, 0.5)";
        delBtn.style.padding = "0 3px";

        const kids = E.childrenOf(box);
        if (kids.length) {
            const fold = document.createElement("span");
            fold.textContent = box._erpkCollapsed ? "▸" : "▾";
            fold.dataset.tip = box._erpkCollapsed
                ? "Expand group" : "Collapse group";
            fold.style.cursor = "pointer";
            fold.style.color = "rgba(255, 255, 255, 0.55)";
            fold.style.flex = "0 0 auto";
            fold.style.width = "10px";
            fold.addEventListener("pointerdown", (e) => e.stopPropagation());
            fold.addEventListener("click", (e) => {
                e.stopPropagation();
                box._erpkCollapsed = !box._erpkCollapsed;
                renderPanelRows();
            });
            row.appendChild(fold);
        } else if (depth > 0 || state.boxes.some((b) => E.childrenOf(b).length)) {
            const pad = document.createElement("span");
            pad.style.flex = "0 0 auto";
            pad.style.width = "10px";
            row.appendChild(pad);
        }
        row.appendChild(rail);
        row.appendChild(eyeBtn);
        row.appendChild(num);
        row.appendChild(plug);
        row.appendChild(refMark);
        row.appendChild(modelMark);
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
            E.toggleRegionHidden(box);
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

    function cutoutDivider() {
        const div = document.createElement("div");
        div.textContent = "cut out · select then ⇧Del to restore · ✕ deletes";
        div.style.font = "8px 'Segoe UI', sans-serif";
        div.style.color = "rgba(255, 255, 255, 0.4)";
        div.style.padding = "5px 5px 2px";
        div.style.marginTop = "3px";
        div.style.borderTop = "1px solid " + HAIRLINE;
        return div;
    }

    // Top row = frontmost region (the end of the array).
    function renderPanelRows() {
        if (!panelList) return;
        panelList.textContent = "";
        const emit = (box, depth) => {
            if (box.cutout) return;  // cut-outs are listed in their own section
            panelList.appendChild(buildPanelRow(box, depth));
            if (box._erpkCollapsed) return;
            const kids = E.childrenOf(box);
            for (let i = kids.length - 1; i >= 0; i--) emit(kids[i], depth + 1);
        };
        const roots = state.boxes.filter((b) => !E.parentRegionOf(b));
        for (let i = roots.length - 1; i >= 0; i--) emit(roots[i], 0);

        // Cut-out regions are pulled from the scene and the layer tree, but must
        // stay reachable or a cut-out is a one-way trap — unselectable on the
        // canvas (boxesAt skips it) and gone from the list. List them flat below.
        const cutouts = state.boxes.filter((b) => b.cutout);
        if (cutouts.length) {
            panelList.appendChild(cutoutDivider());
            for (let i = cutouts.length - 1; i >= 0; i--) {
                panelList.appendChild(buildPanelRow(cutouts[i], 0));
            }
        }
        labelControlsFromTips(panelList);
    }

    function openPanel(e) {
        closePanel();
        E.closeHelp();
        // Right-clicking a region targets it: it becomes the selection and
        // the geometry fields appear; empty canvas opens just the list.
        const hit = E.maskAwareHit(E.pointerNorm(e));
        if (hit >= 0) {
            E.select(state.boxes[hit]);
            E.render();
        }
        const panel = document.createElement("div");
        E.panel = panel;
        panel.className = "erpk-region-list";
        E.popoverZoom(panel);
        // Portaled into document.body as a fixed-position popover so it can
        // spill past the node box. ComfyUI's per-frame transform on the
        // DOM-widget wrapper would otherwise be the containing block for a
        // fixed descendant and re-trap it inside the node (see toolbar.js
        // fullscreen note); body has no such transform, so fixed resolves
        // against the viewport. zIndex sits above the fullscreen overlay (9999).
        panel.style.position = "fixed";
        panel.style.zIndex = "10000";
        panel.style.minWidth = "210px";
        panel.style.maxWidth = "320px";
        panel.style.maxHeight = Math.round(window.innerHeight * 0.8 / E.popoverScale()) + "px";
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

        // The header doubles as a drag handle. The panel is fixed in the
        // viewport, so pointer deltas map 1:1 to left/top — no graph-zoom
        // compensation — and the drag is clamped to the window, not the node.
        header.style.cursor = "grab";
        header.addEventListener("pointerdown", (e) => {
            if (e.button !== 0) return;
            e.preventDefault();
            e.stopPropagation();
            const startLeft = panel.offsetLeft;
            const startTop = panel.offsetTop;
            const startX = e.clientX;
            const startY = e.clientY;
            const move = (ev) => {
                if (!E.panel) return;
                const nx = startLeft + (ev.clientX - startX);
                const ny = startTop + (ev.clientY - startY);
                const pz = E.popoverScale();
                const maxX = Math.max(window.innerWidth - panel.offsetWidth * pz - 4, 0);
                const maxY = Math.max(window.innerHeight - panel.offsetHeight * pz - 4, 0);
                panel.style.left = Math.round(Math.min(Math.max(nx, 4), maxX)) + "px";
                panel.style.top = Math.round(Math.min(Math.max(ny, 4), maxY)) + "px";
            };
            const up = () => {
                document.removeEventListener("pointermove", move);
                document.removeEventListener("pointerup", up);
                header.style.cursor = "grab";
            };
            header.style.cursor = "grabbing";
            document.addEventListener("pointermove", move);
            document.addEventListener("pointerup", up);
        });

        // The detail inspector is built unconditionally and lifted above the
        // list; refreshPanelDetail hides it when nothing is selected, so an
        // empty-canvas right-click still shows just the list, while selecting any
        // row later (including a cut-out, which has no clickable canvas face)
        // reveals it.
        E.buildDetail(panel);

        panelList = document.createElement("div");
        panel.appendChild(panelList);
        renderPanelRows();
        E.refreshPanelDim();
        E.refreshPanelDetail();

        panel.addEventListener("pointerdown", onPanelPointerDown);
        panel.addEventListener("contextmenu", onPanelContextMenu);
        // The panel is portaled out of root, so it needs its own tooltip
        // handlers — root's pointerover never sees these controls.
        panel.addEventListener("pointerover", E.onTipOver);
        panel.addEventListener("pointerout", E.onTipOut);

        // Append to body first so the measured size can clamp the position
        // inside the viewport; the cursor's clientX/Y are already viewport
        // coordinates, so they anchor the fixed popover directly.
        document.body.appendChild(panel);
        labelControlsFromTips(panel);
        const pz = E.popoverScale();
        const maxX = Math.max(window.innerWidth - panel.offsetWidth * pz - 4, 0);
        const maxY = Math.max(window.innerHeight - panel.offsetHeight * pz - 4, 0);
        panel.style.left = Math.round(Math.min(Math.max(e.clientX, 4), maxX)) + "px";
        panel.style.top = Math.round(Math.min(Math.max(e.clientY, 4), maxY)) + "px";

        document.addEventListener("pointerdown", onDocPointerDown, true);
        document.addEventListener("keydown", onDocKeyDown, true);
    }

    // Suppresses both the browser and ComfyUI menus; a second right-click
    // closes the panel.
    function onContextMenu(e) {
        e.preventDefault();
        e.stopPropagation();
        if (E.panel) closePanel();
        else openPanel(e);
    }

    Object.assign(E, {
        closePanel,
        renderPanelRows,
        openPanel,
        onContextMenu,
        deleteRegion,
        onPanelPointerDown,
    });
}
