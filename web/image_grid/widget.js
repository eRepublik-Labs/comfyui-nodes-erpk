// ABOUTME: The image grid DOM widget: a numbered thumbnail grid that picks, drops, reorders,
// ABOUTME: and removes images, and writes the ordered filename list back to the node's `grid_images` widget.
// @ts-check

import { CHROME_HORIZONTAL_INSET } from "../regions/constants.js";
import { findWidget, setWidgetHidden } from "../regions/node_access.js";
import {
    ACCEPTED_LABEL,
    ACCEPTED_TYPES,
    addSummary,
    capacityText,
    countLabel,
    dropPrompt,
    gridLimit,
    moveBy,
    moveItem,
    overCapText,
    parseStoredList,
    planAdd,
    plural,
    remainingSlots,
    removeAt,
} from "./grid_list.js";
import {
    COLUMNS,
    EMPTY_H,
    FOOTER_GAP,
    FOOTER_H,
    GAP,
    HEADER_GAP,
    HEADER_H,
    MIN_NODE_WIDTH,
    NOTICE_H,
    ROOT_PAD_V,
    ZONE_BORDER,
    ZONE_PAD,
} from "./styles.js";

const CELL_DRAG_TYPE = "application/x-erpk-grid-cell";
const KEY_MOVES = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -COLUMNS, ArrowDown: COLUMNS };
let gridSerial = 0;

/**
 * @typedef {{ text: string, tone: "info" | "error", undo?: string[] }} Notice
 * @typedef {{ upload: (file: File) => Promise<string>, imageUrl: (stored: string) => string }} GridIO
 * @typedef {{ name: string, stored: string | null }} Upload
 *   A picked file on its way to ComfyUI's input folder. `stored` is the name the
 *   upload route answered with, null until it answers.
 */

/** @type {Notice} */
const SOCKET_NOTICE = { text: "Image socket connected, grid ignored", tone: "info" };

/**
 * @param {any} node
 * @param {GridIO} io
 * @param {import("./grid_list.js").GridCaps} caps the node's entry from /erpk/grid_caps
 * @param {string} nodeName what an over-cap notice names when the node has no model choice
 */
export function createImageGrid(node, io, caps, nodeName) {
    const serial = ++gridSerial;
    const hintId = `erpk-grid-hint-${serial}`;

    const root = el("div", "erpk-grid-root");
    root.setAttribute("role", "group");
    root.setAttribute("aria-label", "Image grid");
    const zone = el("div", "erpk-grid-zone");
    const header = el("div", "erpk-grid-header");
    const toggle = button("erpk-grid-toggle", "");
    const chevron = el("span", "erpk-grid-chevron");
    chevron.setAttribute("aria-hidden", "true");
    toggle.append(chevron, "Reference images");
    const headerCount = el("span", "erpk-grid-header-count");
    header.append(toggle, headerCount);
    const body = el("div");
    body.id = `erpk-grid-body-${serial}`;
    toggle.setAttribute("aria-controls", body.id);
    const list = el("ol", "erpk-grid-list");
    list.setAttribute("aria-label", "Images in send order");
    const empty = buildEmptyState();
    const footer = el("div", "erpk-grid-footer");
    const capacity = el("span", "erpk-grid-capacity");
    const clearButton = button("erpk-grid-btn erpk-grid-ghost", "Clear all");
    footer.append(capacity, clearButton);
    const overlay = el("div", "erpk-grid-overlay");
    overlay.setAttribute("aria-hidden", "true");
    const overlayTitle = el("span");
    const overlayDetail = el("small");
    overlay.append(overlayTitle, overlayDetail);
    body.append(empty.root, list, footer);
    zone.append(header, body, overlay);

    const notice = el("div", "erpk-grid-notice");
    notice.setAttribute("role", "status");
    const noticeText = el("span", "erpk-grid-notice-text");
    const undoButton = button("erpk-grid-link", "Undo");
    notice.append(noticeText, undoButton);
    const announcer = el("div", "erpk-grid-sr");
    announcer.setAttribute("aria-live", "polite");
    const hint = el("div", "erpk-grid-sr");
    hint.id = hintId;
    hint.textContent = "Arrow keys move this image, Delete removes it.";
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.multiple = true;
    fileInput.accept = ACCEPTED_TYPES.join(",");
    fileInput.hidden = true;
    root.append(zone, notice, announcer, hint, fileInput);
    list.hidden = footer.hidden = notice.hidden = true;

    const state = {
        /** @type {string[]} */
        names: [],
        /** @type {Upload[]} Shown after `names`, in drop order, until each lands in it. */
        uploads: [],
        /** @type {Notice | null} */
        notice: null,
        /** @type {number | null} */
        dragFrom: null,
        /** @type {(() => void) | null} */
        refocus: null,
        ready: false,
        socketLinked: false,
        collapsed: false,
    };
    // Uploads run in parallel, but a finished one joins `names` only once every
    // earlier one has, so the list keeps drop order. Batch summaries follow the
    // same order.
    let summaries = Promise.resolve();

    function requireWidget(name) {
        const widget = findWidget(node, name);
        if (!widget) throw new Error(`${node.type} node ${node.id} has no ${name} widget`);
        return widget;
    }

    function imagesWidget() {
        return requireWidget("grid_images");
    }

    function currentLimit() {
        const model = caps.model_widget ? requireWidget(caps.model_widget).value : undefined;
        return gridLimit(caps, model, nodeName);
    }

    function maxImages() {
        return currentLimit().cap;
    }

    /** Slots taken: stored images plus the uploads still on their way. */
    function filled() {
        return state.names.length + state.uploads.length;
    }

    function setup() {
        if (state.ready) return;
        state.ready = true;
        const images = imagesWidget();
        setWidgetHidden(images, true);
        images.computeSize = () => [0, -4];
        if (images.inputEl) images.inputEl.style.display = "none";
        if (images.element) images.element.style.display = "none";
        if (caps.model_widget) {
            const model = requireWidget(caps.model_widget);
            const onModelChange = model.callback;
            model.callback = function () {
                const r = onModelChange?.apply(this, arguments);
                render();
                return r;
            };
        }
        loadFromWidget();
    }

    function loadFromWidget() {
        const stored = parseStoredList(imagesWidget().value);
        state.names = stored.names;
        state.notice = stored.error ? { text: stored.error, tone: "error" } : null;
        render();
    }

    /** @param {string[]} names @param {{ notice?: Notice | null, announce?: string }} [effects] */
    function commit(names, { notice = null, announce = "" } = {}) {
        state.names = names;
        state.notice = notice;
        const widget = imagesWidget();
        widget.value = JSON.stringify(names);
        widget.callback?.(widget.value);
        announcer.textContent = announce;
        render();
        node.setDirtyCanvas?.(true, true);
    }

    function render() {
        const cap = maxImages();
        const count = filled();
        empty.root.hidden = count > 0;
        list.hidden = count === 0;
        footer.hidden = count === 0;
        empty.limit.textContent = `Up to ${plural(cap, "image")} · ${ACCEPTED_LABEL}`;
        list.replaceChildren(
            ...state.names.map((name, index) => buildCell(name, index, count)),
            ...state.uploads.map((upload, index) => buildUploadCell(upload, state.names.length + index, count)),
        );
        if (remainingSlots(count, cap) > 0) list.append(buildAddCell());
        capacity.textContent = capacityText(count, cap);
        capacity.classList.toggle("erpk-grid-over-cap", count > cap);
        headerCount.textContent = countLabel(count, cap);
        headerCount.classList.toggle("erpk-grid-over-cap", count > cap);
        body.hidden = state.collapsed;
        chevron.textContent = state.collapsed ? "▸" : "▾";
        toggle.setAttribute("aria-expanded", String(!state.collapsed));
        zone.classList.toggle("erpk-grid-collapsed", state.collapsed);
        clearButton.disabled = state.uploads.length > 0;
        zone.classList.toggle("erpk-grid-ignored", state.socketLinked);
        setDisabled(empty.choose, state.socketLinked);
        const shown = currentNotice();
        notice.hidden = shown === null;
        noticeText.textContent = shown?.text ?? "";
        noticeText.title = shown?.text ?? "";
        notice.classList.toggle("erpk-grid-error", shown?.tone === "error");
        undoButton.hidden = !shown?.undo;
        layout();
        fitNodeHeight();
        const refocus = state.refocus;
        state.refocus = null;
        refocus?.();
    }

    // A notice from the user's last action outranks the socket notice, so
    // Clear all keeps its Undo while the socket is linked. While the grid is
    // live, holding more than its limit outranks both: it is why drops are
    // refused, and it stays until the list fits.
    /** @returns {Notice | null} */
    function currentNotice() {
        if (state.socketLinked) return state.notice ?? SOCKET_NOTICE;
        const overCap = state.ready ? overCapText(filled(), currentLimit()) : null;
        return overCap ? { text: overCap, tone: "error" } : state.notice;
    }

    /** @param {boolean} linked */
    function setSocketLinked(linked) {
        if (state.socketLinked === linked) return;
        state.socketLinked = linked;
        if (linked) state.notice = null;
        if (!state.ready) return;
        render();
        node.setDirtyCanvas?.(true, true);
    }

    /** @param {boolean} collapsed */
    function setCollapsed(collapsed) {
        state.collapsed = collapsed;
        if (state.ready) render();
    }

    // Only a user's choice is written, so a grid nobody has collapsed saves no
    // property and loads expanded.
    /** @param {boolean} collapsed */
    function chooseCollapsed(collapsed) {
        node.properties = node.properties || {};
        node.properties.erpkGridCollapsed = collapsed;
        setCollapsed(collapsed);
        node.setDirtyCanvas?.(true, true);
    }

    function layout() {
        root.style.width = `${rootWidth()}px`;
    }

    function rootWidth() {
        return Math.max((node.size?.[0] ?? MIN_NODE_WIDTH) - CHROME_HORIZONTAL_INSET, 100);
    }

    // The DOM widget pins min == max height to this, so the node grows a row at
    // a time as images arrive. Mirrors the CSS box model in styles.js.
    function desiredHeight() {
        const noticeH = currentNotice() ? NOTICE_H : 0;
        if (state.collapsed) return HEADER_H + 2 * ZONE_PAD + 2 * ZONE_BORDER + noticeH + ROOT_PAD_V;
        const headerH = HEADER_H + HEADER_GAP;
        const count = filled();
        if (count === 0) return EMPTY_H + headerH + noticeH + ROOT_PAD_V;
        const inner = rootWidth() - 2 * ZONE_PAD - 2 * ZONE_BORDER;
        const cell = (inner - GAP * (COLUMNS - 1)) / COLUMNS;
        const cells = count + (remainingSlots(count, maxImages()) > 0 ? 1 : 0);
        const rows = Math.ceil(cells / COLUMNS);
        const grid = rows * cell + (rows - 1) * GAP;
        const zoneH = headerH + grid + 2 * ZONE_PAD + 2 * ZONE_BORDER + FOOTER_GAP + FOOTER_H;
        return Math.ceil(zoneH + noticeH + ROOT_PAD_V);
    }

    function fitNodeHeight() {
        const size = node.computeSize?.();
        if (size && node.size && node.size[1] !== size[1]) node.setSize([node.size[0], size[1]]);
    }

    /** Null until setup has found the node's widgets, and while the socket is linked. */
    function titleCount() {
        if (!state.ready || state.socketLinked) return null;
        const cap = maxImages();
        return { text: countLabel(filled(), cap), overCap: filled() > cap };
    }

    function buildCell(name, index, count) {
        const cell = el("li", "erpk-grid-cell");
        cell.tabIndex = 0;
        cell.draggable = true;
        cell.dataset.index = String(index);
        cell.title = name;
        cell.setAttribute("aria-label", `Image ${index + 1} of ${count}, ${name}`);
        cell.setAttribute("aria-describedby", hintId);
        const missing = el("span", "erpk-grid-missing");
        missing.textContent = "Missing";
        const remove = button("erpk-grid-remove", "×");
        remove.tabIndex = -1;
        remove.dataset.remove = String(index);
        remove.setAttribute("aria-label", `Remove image ${index + 1}`);
        cell.append(thumbnail(name, cell), missing, cellBadge(index), remove);
        return cell;
    }

    // Not focusable or draggable, and it has no data-index, so a reorder drop
    // on it appends after the stored images.
    /** @param {Upload} upload @param {number} index @param {number} count */
    function buildUploadCell(upload, index, count) {
        const cell = el("li", "erpk-grid-cell erpk-grid-pending");
        cell.title = upload.name;
        cell.setAttribute("aria-busy", "true");
        const status = upload.stored === null ? "uploading" : "uploaded, waiting for earlier files";
        cell.setAttribute("aria-label", `Image ${index + 1} of ${count}, ${upload.name}, ${status}`);
        if (upload.stored === null) {
            cell.classList.add("erpk-grid-uploading");
            const spinner = el("span", "erpk-grid-spinner");
            spinner.setAttribute("aria-hidden", "true");
            cell.append(spinner, cellBadge(index));
        } else {
            cell.append(thumbnail(upload.stored, cell), cellBadge(index));
        }
        return cell;
    }

    /** @param {string} stored @param {HTMLElement} cell */
    function thumbnail(stored, cell) {
        const img = document.createElement("img");
        img.alt = "";
        img.decoding = "async";
        img.loading = "lazy";
        img.draggable = false;
        img.addEventListener("error", () => {
            // ComfyUI cannot preview a PNG with an edge over WebP's 16383 px; show it as stored.
            const url = new URL(img.src);
            if (url.searchParams.has("preview")) {
                url.searchParams.delete("preview");
                img.src = url.href;
                return;
            }
            cell.classList.add("erpk-grid-is-missing");
        });
        img.src = io.imageUrl(stored);
        return img;
    }

    /** @param {number} index */
    function cellBadge(index) {
        const badge = el("span", "erpk-grid-badge");
        badge.setAttribute("aria-hidden", "true");
        badge.textContent = String(index + 1);
        return badge;
    }

    function buildAddCell() {
        const item = el("li");
        const add = button("erpk-grid-add", "");
        add.setAttribute("aria-label", "Add images");
        const plus = el("span", "erpk-grid-plus");
        plus.setAttribute("aria-hidden", "true");
        plus.textContent = "+";
        add.append(plus, "Add");
        setDisabled(add, state.socketLinked);
        add.addEventListener("click", openPicker);
        item.append(add);
        return item;
    }

    function openPicker() {
        fileInput.click();
    }

    /** @param {File[]} files */
    function addFiles(files) {
        if (files.length === 0 || state.socketLinked) return;
        const plan = planAdd(files, filled(), maxImages());
        if (plan.take.length === 0) {
            state.notice = { text: addSummary({ added: 0, ...plan, failures: [] }), tone: "error" };
            render();
            return;
        }
        if (state.collapsed) chooseCollapsed(false);
        /** @type {Upload[]} */
        const batch = plan.take.map((file) => ({ name: file.name, stored: null }));
        /** @type {(string | null)[]} */
        const failed = batch.map(() => null);
        state.uploads.push(...batch);
        state.notice = { text: `Uploading ${plural(batch.length, "image")}…`, tone: "info" };
        render();
        const settled = plan.take.map((file, i) => io.upload(file).then(
            (stored) => {
                batch[i].stored = stored;
                landUploads();
            },
            (error) => {
                failed[i] = String(error?.message ?? error);
                state.uploads = state.uploads.filter((upload) => upload !== batch[i]);
                state.notice = { text: failed[i], tone: "error" };
                landUploads();
            },
        ));
        summaries = summaries.then(() => Promise.all(settled)).then(() => {
            const failures = failed.filter((text) => text !== null);
            const added = batch.length - failures.length;
            const text = addSummary({ added, overflow: plan.overflow, wrongType: plan.wrongType, failures });
            state.notice = { text, tone: failures.length > 0 ? "error" : "info" };
            announcer.textContent = text;
            render();
        });
    }

    // Moves finished uploads at the head of the queue into the list.
    function landUploads() {
        const landed = [];
        while (state.uploads.length > 0 && state.uploads[0].stored !== null) {
            landed.push(state.uploads.shift().stored);
        }
        if (landed.length > 0) commit([...state.names, ...landed], { notice: state.notice });
        else render();
    }

    function removeImage(index, { keepFocus }) {
        const next = removeAt(state.names, index);
        if (keepFocus) state.refocus = () => focusCellOrAdd(Math.min(index, next.length - 1));
        commit(next, { announce: `Removed image ${index + 1}. ${plural(next.length, "image")} left.` });
    }

    function focusCellOrAdd(index) {
        const target = list.querySelector(`[data-index="${index}"]`)
            ?? list.querySelector(".erpk-grid-add")
            ?? empty.choose;
        if (target instanceof HTMLElement) target.focus();
    }

    function clearAll() {
        const previous = state.names;
        state.refocus = () => undoButton.focus();
        commit([], {
            notice: {
                text: `Cleared ${plural(previous.length, "image")}. The files stay in ComfyUI's input folder.`,
                tone: "info",
                undo: previous,
            },
        });
    }

    function undoClear() {
        const previous = state.notice?.undo;
        if (!previous) return;
        state.refocus = () => focusCellOrAdd(0);
        commit(previous, { announce: `Restored ${plural(previous.length, "image")}.` });
    }

    function insertionTarget(e) {
        const item = e.target instanceof Element ? e.target.closest("li") : null;
        if (!item || !list.contains(item)) return null;
        if (item.dataset.index === undefined) {
            return { insertAt: state.names.length, cell: state.names.length - 1, side: "after" };
        }
        const index = Number(item.dataset.index);
        const rect = item.getBoundingClientRect();
        return e.clientX < rect.left + rect.width / 2
            ? { insertAt: index, cell: index, side: "before" }
            : { insertAt: index + 1, cell: index, side: "after" };
    }

    function clearInsertionMarks() {
        for (const cell of list.querySelectorAll(".erpk-grid-insert-before, .erpk-grid-insert-after")) {
            cell.classList.remove("erpk-grid-insert-before", "erpk-grid-insert-after");
        }
    }

    function isCellDrag(e) {
        return state.dragFrom !== null && (e.dataTransfer?.types?.includes(CELL_DRAG_TYPE) ?? false);
    }

    function onCellDragStart(e) {
        const cell = e.target instanceof Element ? e.target.closest(".erpk-grid-cell") : null;
        if (!(cell instanceof HTMLElement) || !e.dataTransfer) return;
        e.stopPropagation();
        state.dragFrom = Number(cell.dataset.index);
        e.dataTransfer.setData(CELL_DRAG_TYPE, String(state.dragFrom));
        e.dataTransfer.effectAllowed = "move";
        cell.classList.add("erpk-grid-dragging");
        root.classList.add("erpk-grid-reordering");
    }

    function onCellDragOver(e) {
        if (!isCellDrag(e)) return;
        e.preventDefault();
        e.stopPropagation();
        e.dataTransfer.dropEffect = "move";
        const target = insertionTarget(e);
        if (!target) return;
        clearInsertionMarks();
        const from = state.dragFrom;
        if (target.insertAt === from || target.insertAt === from + 1) return;
        list.querySelector(`[data-index="${target.cell}"]`)?.classList.add(`erpk-grid-insert-${target.side}`);
    }

    function onCellDrop(e) {
        if (!isCellDrag(e)) return;
        e.preventDefault();
        e.stopPropagation();
        const from = state.dragFrom;
        const target = insertionTarget(e);
        endCellDrag();
        if (!target) return;
        const moved = moveItem(state.names, from, target.insertAt);
        if (moved.index === from) return;
        commit(moved.names, { announce: `Moved image to position ${moved.index + 1} of ${moved.names.length}.` });
    }

    function endCellDrag() {
        state.dragFrom = null;
        clearInsertionMarks();
        list.querySelector(".erpk-grid-dragging")?.classList.remove("erpk-grid-dragging");
        root.classList.remove("erpk-grid-reordering");
    }

    // ComfyUI binds Delete and Backspace on window to delete the selected node,
    // so every key handled here stops before it bubbles that far.
    function onCellKeydown(e) {
        const cell = e.target;
        if (!(cell instanceof HTMLElement) || !cell.classList.contains("erpk-grid-cell")) return;
        if (e.altKey || e.ctrlKey || e.metaKey) return;
        const index = Number(cell.dataset.index);
        if (e.key === "Delete" || e.key === "Backspace") {
            removeImage(index, { keepFocus: true });
        } else if (e.key in KEY_MOVES) {
            const moved = moveBy(state.names, index, KEY_MOVES[e.key]);
            if (moved.index !== index) {
                state.refocus = () => focusCellOrAdd(moved.index);
                commit(moved.names, { announce: `Moved image to position ${moved.index + 1} of ${moved.names.length}.` });
            }
        } else {
            return;
        }
        e.preventDefault();
        e.stopPropagation();
    }

    function onListClick(e) {
        const remove = e.target instanceof Element ? e.target.closest("[data-remove]") : null;
        if (!(remove instanceof HTMLElement)) return;
        removeImage(Number(remove.dataset.remove), { keepFocus: false });
    }

    // ComfyUI loads a workflow from any image dropped on the page, so a file
    // drop that lands on the grid must stop here.

    function isFileDrag(e) {
        return e.dataTransfer?.types?.includes("Files") ?? false;
    }

    /** Null when the browser hides the dragged files' types until the drop. */
    function draggedImageCount(dataTransfer) {
        const files = [...(dataTransfer.items ?? [])].filter((item) => item.kind === "file");
        if (files.length === 0 || files.some((item) => item.type === "")) return null;
        return files.filter((item) => ACCEPTED_TYPES.includes(item.type)).length;
    }

    function onFileDragOver(e) {
        if (!isFileDrag(e)) return;
        e.preventDefault();
        e.stopPropagation();
        if (state.socketLinked) {
            e.dataTransfer.dropEffect = "none";
            return;
        }
        const prompt = dropPrompt(draggedImageCount(e.dataTransfer), filled(), maxImages());
        e.dataTransfer.dropEffect = prompt.full ? "none" : "copy";
        overlayTitle.textContent = prompt.title;
        overlayDetail.textContent = prompt.detail;
        zone.classList.add("erpk-grid-over");
        zone.classList.toggle("erpk-grid-refuse", prompt.full);
    }

    function onFileDragLeave(e) {
        if (!isFileDrag(e)) return;
        if (e.relatedTarget instanceof Node && root.contains(e.relatedTarget)) return;
        zone.classList.remove("erpk-grid-over", "erpk-grid-refuse");
    }

    function onFileDrop(e) {
        if (!isFileDrag(e)) return;
        e.preventDefault();
        e.stopPropagation();
        zone.classList.remove("erpk-grid-over", "erpk-grid-refuse");
        addFiles([...e.dataTransfer.files]);
    }

    // A press on the grid belongs to the grid, not to the node's own
    // select-and-drag handling around the DOM widget.
    zone.addEventListener("pointerdown", (e) => e.stopPropagation());
    fileInput.addEventListener("change", () => {
        const files = [...(fileInput.files ?? [])];
        fileInput.value = "";
        addFiles(files);
    });
    toggle.addEventListener("click", () => chooseCollapsed(!state.collapsed));
    empty.choose.addEventListener("click", openPicker);
    clearButton.addEventListener("click", clearAll);
    undoButton.addEventListener("click", undoClear);
    list.addEventListener("click", onListClick);
    list.addEventListener("keydown", onCellKeydown);
    list.addEventListener("dragstart", onCellDragStart);
    list.addEventListener("dragover", onCellDragOver);
    list.addEventListener("drop", onCellDrop);
    list.addEventListener("dragend", endCellDrag);
    root.addEventListener("dragenter", onFileDragOver);
    root.addEventListener("dragover", onFileDragOver);
    root.addEventListener("dragleave", onFileDragLeave);
    root.addEventListener("drop", onFileDrop);

    return { root, setup, loadFromWidget, layout, desiredHeight, titleCount, addFiles, setSocketLinked, setCollapsed };
}

/** @param {HTMLButtonElement} control @param {boolean} disabled */
function setDisabled(control, disabled) {
    control.disabled = disabled;
    if (disabled) control.setAttribute("aria-disabled", "true");
    else control.removeAttribute("aria-disabled");
}

function buildEmptyState() {
    const root = el("div", "erpk-grid-empty");
    const icon = el("div", "erpk-grid-icon");
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = "↧";
    const primary = el("div", "erpk-grid-primary");
    primary.textContent = "Drop images here";
    const limit = el("div");
    const choose = button("erpk-grid-btn", "Choose files…");
    root.append(icon, primary, limit, choose);
    return { root, limit, choose };
}

/** @param {string} tag @param {string} [className] */
function el(tag, className) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    return node;
}

/** @param {string} className @param {string} label */
function button(className, label) {
    const node = document.createElement("button");
    node.type = "button";
    node.className = className;
    node.textContent = label;
    return node;
}
