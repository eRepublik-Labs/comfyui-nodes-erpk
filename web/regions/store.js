// ABOUTME: Editor state, selection, undo/redo, layer-group normalization, and region mutations.
// ABOUTME: Reads/writes the regions_data widget through schema.js; the render callback is injected via E.
// @ts-check

import { clamp } from "./geometry.js";
import { findWidget } from "./node_access.js";
import { serializeRegions, deserializeRegions } from "./schema.js";

import {
    GRID_DEFAULT_CELL_PX,
    GRID_DEFAULT_COLOR,
} from "./constants.js";

// Copy buffer of plain region data; module-level so clones carry between
// editor instances within the page session.
let regionClipboard = [];

export function createState() {
    return {
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
        scanCost: null,        // last scan's {usd, input_tokens, output_tokens, calls, model}
        scanSessionUsd: 0,     // running cost of priced scans since the editor opened
    };
}

export function installStore(E) {
    const { node, state } = E;

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
        state.boxes = deserializeRegions(snapshot);
        clearSelection();
        undoRestoring = true;
        syncWidget();
        undoRestoring = false;
        E.render();
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
        state.boxes = deserializeRegions(widget?.value ?? "[]");
        // A (re)loaded workflow is a fresh document; stale history would
        // restore another graph's regions.
        undoStack.length = 0;
        redoStack.length = 0;
        clearSelection();
        E.render();
    }

    // --- Layer groups: stable ids, parent links, tree walks -----------
    function regionId(box) {
        if (!box.id) box.id = Math.random().toString(36).slice(2, 8);
        return box.id;
    }

    function parentRegionOf(box) {
        if (!box?.parent) return null;
        return state.boxes.find((b) => b.id === box.parent) || null;
    }

    function childrenOf(box) {
        if (!box?.id) return [];
        return state.boxes.filter((b) => b.parent === box.id);
    }

    function descendantsOf(box, out = []) {
        for (const child of childrenOf(box)) {
            out.push(child);
            descendantsOf(child, out);
        }
        return out;
    }

    function isDescendantOf(box, ancestor) {
        let cur = parentRegionOf(box);
        while (cur) {
            if (cur === ancestor) return true;
            cur = parentRegionOf(cur);
        }
        return false;
    }

    // Hidden inherits down the tree, like every layers palette.
    function effectiveHidden(box) {
        let cur = box;
        while (cur) {
            if (cur.hidden) return true;
            cur = parentRegionOf(cur);
        }
        return false;
    }

    // Rebuilds the z-array so each parent is immediately followed by its
    // descendants (group contiguity), preserving relative order throughout.
    function normalizeGroups(order) {
        const out = [];
        const visit = (box) => {
            out.push(box);
            for (const child of order.filter((c) => parentRegionOf(c) === box)) {
                visit(child);
            }
        };
        for (const box of order) {
            if (!parentRegionOf(box)) visit(box);
        }
        return out.length === order.length ? out : order;
    }

    // True when the region's geometry has left its scan origin box.
    function regionMoved(box) {
        if (!box.src) return false;
        return ["x", "y", "w", "h"].some(
            (k) => Math.abs(box.src[k] - box[k]) > 0.005,
        );
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
        for (const box of state.selection) {
            for (const child of childrenOf(box)) {
                if (state.selection.has(child)) continue;
                let p = parentRegionOf(box);
                while (p && state.selection.has(p)) p = parentRegionOf(p);
                if (p) child.parent = regionId(p);
                else delete child.parent;
            }
        }
        state.boxes = state.boxes.filter((b) => !state.selection.has(b));
        clearSelection();
        syncWidget();
        E.render();
    }

    // Shift+Delete: toggle the selection's cut-out state. Cutting out removes a
    // region from the scene and erases it to transparent in the image output,
    // shown on the canvas as the transparency checker behind the mask; toggling
    // it back restores a normal region. If the selection is mixed, cut all out.
    // Undoable like any region change (Ctrl/Cmd+Z).
    function cutoutSelected() {
        if (!state.selection.size) return;
        const allCut = [...state.selection].every((box) => box.cutout);
        for (const box of state.selection) box.cutout = !allCut;
        clearSelection();
        syncWidget();
        E.render();
    }

    // Set who applies a region's geometric edit: "model" (the edit model does the
    // move/cut-out from the prompt) or "node" (the deterministic composite/inpaint,
    // the default, stored as the field's absence).
    function setRegionEditBy(box, mode) {
        if (!box) return;
        if (mode === "model") box.edit_by = "model";
        else delete box.edit_by;
        syncWidget();
        E.render();
    }

    // Appends clones of the given regions on top (frontmost), nudged so the
    // copies read as distinct from their sources, and selects them.
    function pasteRegions(source) {
        if (!source.length) return;
        // Map each source region to its clone so parent links rewire to the
        // copies, not the originals.
        const cloneByOldId = new Map();
        const pasted = source.map((b) => {
            const copy = {
                ...b,
                x: clamp(b.x + 0.02, 0, 1 - b.w),
                y: clamp(b.y + 0.02, 0, 1 - b.h),
            };
            delete copy.id;  // clones must not share the source's identity
            if (b.id) cloneByOldId.set(b.id, copy);
            return copy;
        });
        // Repoint each clone's parent at the pasted parent when it was copied
        // too; otherwise drop it — a paste is self-contained and must not
        // re-attach to the source group it was lifted from.
        for (const copy of pasted) {
            if (!copy.parent) continue;
            const parentClone = cloneByOldId.get(copy.parent);
            if (parentClone) copy.parent = regionId(parentClone);
            else delete copy.parent;
        }
        state.boxes.push(...pasted);
        state.selection = new Set(pasted);
        state.primary = pasted[pasted.length - 1];
        syncWidget();
        E.render();
    }

    // Clipboard copy/paste of the current selection, kept module-level so the
    // buffer survives between editor instances on the page.
    function copySelection() {
        regionClipboard = selectionInOrder().map((b) => ({ ...b }));
    }

    function clipboardSize() {
        return regionClipboard.length;
    }

    function pasteClipboard() {
        if (regionClipboard.length) pasteRegions(regionClipboard);
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
        E.render();
    }

    // Per-region visibility: a hidden region skips drawing and hit-testing but
    // still feeds the prompt and mask outputs.
    function toggleRegionHidden(box) {
        if (!box) return;
        box.hidden = !box.hidden;
        syncWidget();
        E.render();
    }

    Object.assign(E, {
        syncWidget,
        restoreSnapshot,
        undoRegions,
        redoRegions,
        loadFromWidget,
        regionId,
        parentRegionOf,
        childrenOf,
        descendantsOf,
        isDescendantOf,
        effectiveHidden,
        normalizeGroups,
        regionMoved,
        primaryIndex,
        lastSelected,
        select,
        clearSelection,
        selectionInOrder,
        deleteSelected,
        cutoutSelected,
        setRegionEditBy,
        pasteRegions,
        copySelection,
        clipboardSize,
        pasteClipboard,
        moveRegion,
        moveSelectedRegion,
        toggleRegionHidden,
    });
}
