// ABOUTME: The right-click region list panel — rows front-to-back with select, duplicate, delete, drag-reorder.
// ABOUTME: Hosts the detail section (built by properties) and groups; mutations flow through the injected E.

import { clamp, regionColor } from "./geometry.js";
import { makeStripButton, setEyeIcon } from "./styles.js";
import {
    HAIRLINE,
    HAIRLINE_STRONG,
    PANEL_BG,
    DANGER_RED_DIM,
    DANGER_RED_BORDER,
} from "./constants.js";

export function installLayers(E) {
    const { state, root, canvas } = E;

    let panelList = null;

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
        if (!E.panel) return;
        document.removeEventListener("pointerdown", onDocPointerDown, true);
        document.removeEventListener("keydown", onDocKeyDown, true);
        E.panel.remove();
        E.panel = null;
        panelList = null;
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
        row._erpkBox = box;
        row.className = "erpk-region-row";
        row.style.display = "flex";
        row.style.alignItems = "center";
        row.style.gap = "5px";
        row.style.padding = "2px 5px";
        row.style.paddingLeft = (5 + depth * 14) + "px";
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
        plug.style.display = E.descWiredFor(box) ? "" : "none";

        const refMark = document.createElement("span");
        refMark.style.flex = "0 0 auto";
        refMark.style.color = regionColor(index);
        refMark.dataset.tip = "Reference image wired from a ref input";
        refMark.textContent = "▣";
        refMark.style.display = E.refWiredFor(box) ? "" : "none";

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
        setEyeIcon(eyeBtn, E.effectiveHidden(box));
        if (E.effectiveHidden(box) && !box.hidden) eyeBtn.style.opacity = "0.55";
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

    // Top row = frontmost region (the end of the array).
    function renderPanelRows() {
        if (!panelList) return;
        panelList.textContent = "";
        const emit = (box, depth) => {
            if (box.cutout) return;  // cut-out regions are removed from the list
            panelList.appendChild(buildPanelRow(box, depth));
            if (box._erpkCollapsed) return;
            const kids = E.childrenOf(box);
            for (let i = kids.length - 1; i >= 0; i--) emit(kids[i], depth + 1);
        };
        const roots = state.boxes.filter((b) => !E.parentRegionOf(b));
        for (let i = roots.length - 1; i >= 0; i--) emit(roots[i], 0);
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

        // The header doubles as a drag handle; clientX deltas are scaled
        // back through the graph zoom like panelPoint does.
        header.style.cursor = "grab";
        header.addEventListener("pointerdown", (e) => {
            if (e.button !== 0) return;
            e.preventDefault();
            e.stopPropagation();
            const startLeft = panel.offsetLeft;
            const startTop = panel.offsetTop;
            const startX = e.clientX;
            const startY = e.clientY;
            const r = root.getBoundingClientRect();
            const scale = r.width ? root.offsetWidth / r.width : 1;
            const move = (ev) => {
                if (!E.panel) return;
                const nx = startLeft + (ev.clientX - startX) * scale;
                const ny = startTop + (ev.clientY - startY) * scale;
                const pz = E.popoverScale();
                const maxX = Math.max(root.clientWidth - panel.offsetWidth * pz - 4, 0);
                const maxY = Math.max(root.clientHeight - panel.offsetHeight * pz - 4, 0);
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

        // Right-clicking a region shows its detail above the list. Empty-canvas
        // right-clicks open just the list.
        if (hit >= 0) {
            E.buildDetail(panel);
        }

        panelList = document.createElement("div");
        panel.appendChild(panelList);
        renderPanelRows();
        E.refreshPanelDim();
        E.refreshPanelDetail();

        panel.addEventListener("pointerdown", onPanelPointerDown);
        panel.addEventListener("contextmenu", onPanelContextMenu);

        // Append first so the measured size can clamp the position fully
        // inside the root.
        root.appendChild(panel);
        const pt = panelPoint(e);
        const pz = E.popoverScale();
        const maxX = Math.max(root.clientWidth - panel.offsetWidth * pz - 4, 0);
        const maxY = Math.max(root.clientHeight - panel.offsetHeight * pz - 4, 0);
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
