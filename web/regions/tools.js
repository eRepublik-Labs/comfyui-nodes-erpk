// ABOUTME: Pointer, keyboard, and inspector-input interactions — select, draw, move, resize, marquee.
// ABOUTME: Hit testing and snapping live here; mutations and rendering are reached through the injected E.
// @ts-check

import { clamp, rectFrom, enforceMinSize } from "./geometry.js";
import { frameDims } from "./node_access.js";
import { maskPixelHit } from "./masks.js";
import { HANDLE_HIT_PX, MIN_REGION_SIZE } from "./constants.js";

export function installTools(E) {
    const { node, state, canvas, descInput, kindSelect, textInput,
            backBtn, frontBtn } = E;

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
        for (const handle of E.cornerHandles(box)) {
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
            if (E.effectiveHidden(b) || b.cutout) continue;
            if (p.x >= b.x && p.x <= b.x + b.w && p.y >= b.y && p.y <= b.y + b.h) {
                hits.push(b);
            }
        }
        return hits;
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
        if (state.scanning) {
            canvas.style.cursor = "wait";
            return;
        }
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

    function snapAxis(v, framePx) {
        if (!(state.gridShow && state.snapOn)) return v;
        const cell = state.gridCellPx;
        return clamp((Math.round((v * framePx) / cell) * cell) / framePx, 0, 1);
    }

    function snapPoint(p) {
        const dims = frameDims(node);
        return { x: snapAxis(p.x, dims.w), y: snapAxis(p.y, dims.h) };
    }

    // --- Event handlers ----------------------------------------------------
    function onPointerDown(e) {
        if (e.button !== 0) return;
        e.stopPropagation();
        // A scan is in flight: swallow the event so nothing draws, selects, or
        // moves while the regions are about to be replaced. The cursor shows the
        // busy state (updateCursor and the renderer set it to "wait").
        if (state.scanning) return;
        // A canvas interaction acknowledges any lingering scan error, so a past
        // failure clears instead of pinning in the status strip across edits.
        if (state.scanError) state.scanError = null;
        canvas.focus();
        canvas.setPointerCapture(e.pointerId);

        const p = pointerNorm(e);

        // Ctrl/Cmd forces a fresh box even when the drag starts over one.
        if (e.ctrlKey || e.metaKey) {
            E.clearSelection();
            const anchor = snapPoint(p);
            state.drag = { mode: "create", anchor, current: anchor };
            E.render();
            return;
        }

        // A corner handle of the selected region takes priority over Shift and
        // Alt, so Shift+handle starts a proportional resize (constrained live in
        // onPointerMove) instead of falling through to a marquee. hitHandle only
        // fires when exactly one region is selected.
        const handleId = hitHandle(pointerPx(e));
        if (handleId) {
            const box = state.primary;
            state.drag = {
                mode: "resize", box,
                anchor: resizeAnchor(box, handleId),
                // Aspect at grab time, for Shift-constrained resizing.
                aspect: box.h > 0 ? box.w / box.h : 1,
            };
            E.render();
            return;
        }

        // Shift toggles membership on a box, or starts a marquee on empty
        // canvas.
        if (e.shiftKey) {
            const hit = maskAwareHit(p);
            if (hit >= 0) {
                E.select(state.boxes[hit], { toggle: true });
            } else {
                state.drag = { mode: "marquee", anchor: p, current: p };
            }
            E.render();
            return;
        }

        // Alt cycles through the stack under the pointer, topmost first;
        // with nothing underneath it falls through to the plain behavior.
        if (e.altKey && !state.hideBoxes) {
            const hits = boxesAt(p);
            if (hits.length) {
                const idx = hits.indexOf(state.primary);
                E.select(hits[(idx + 1) % hits.length]);
                E.render();
                return;
            }
        }

        // Handles and modifiers were resolved above; what remains is a plain
        // press — select/move a region, cancel a move ghost, or start a new box.
        {
            const hit = maskAwareHit(p);
            if (hit >= 0) {
                const box = state.boxes[hit];
                const wasSelected = state.selection.has(box);
                if (wasSelected) {
                    state.primary = box;
                } else {
                    E.select(box);
                }
                const moving = new Set(state.selection);
                for (const sel of state.selection) {
                    for (const d of E.descendantsOf(sel)) moving.add(d);
                }
                state.drag = {
                    mode: "move",
                    grabDX: p.x - box.x,
                    grabDY: p.y - box.y,
                    startX: box.x,
                    startY: box.y,
                    starts: new Map(
                        [...moving].map((b) => [b, { x: b.x, y: b.y }]),
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
                    (b) => b.mask && E.regionMoved(b)
                        && p.x >= b.src.x && p.x <= b.src.x + b.src.w
                        && p.y >= b.src.y && p.y <= b.src.y + b.src.h,
                );
                if (ghost) {
                    Object.assign(ghost, {
                        x: ghost.src.x, y: ghost.src.y,
                        w: ghost.src.w, h: ghost.src.h,
                    });
                    E.select(ghost);
                    E.syncWidget();
                    E.render();
                    return;
                }
                E.clearSelection();
                const anchor = snapPoint(p);
                state.drag = { mode: "create", anchor, current: anchor };
            }
        }
        E.render();
    }

    function onPointerMove(e) {
        if (!state.drag) {
            updateCursor(e);
            E.trackRegionTip(e);
            const hover = maskAwareHit(pointerNorm(e));
            if (hover !== state.hoverIndex) {
                state.hoverIndex = hover;
                E.render();
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
        E.render();
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
                // Hand-drawn regions are additions the edit model places, so they
                // default to Model. Scanned regions (which become moves, where a
                // deterministic composite is the better default) keep Node.
                const box = { ...rect, kind: "object", desc: "", text: "",
                              edit_by: "model" };
                state.boxes.push(box);
                E.select(box);
                E.syncWidget();
            }
        } else if (d.mode === "marquee") {
            const rect = rectFrom(d.anchor, d.current);
            // Same visibility guard as boxesAt/drawBox: a marquee must not grab
            // hidden or cut-out regions, or edits would bind to ones the user
            // can't see on the canvas.
            const hits = state.boxes.filter((b) =>
                !E.effectiveHidden(b) && !b.cutout
                && b.x <= rect.x + rect.w && b.x + b.w >= rect.x
                && b.y <= rect.y + rect.h && b.y + b.h >= rect.y);
            state.selection = new Set(hits);
            state.primary = hits.length ? hits[hits.length - 1] : null;
        } else if (d.mode === "move") {
            if (!d.moved && d.collapseTo) {
                E.select(d.collapseTo);
            } else {
                for (const box of d.starts.keys()) enforceMinSize(box);
                E.syncWidget();
            }
        } else if (d.mode === "resize") {
            if (d.box) {
                enforceMinSize(d.box);
                E.syncWidget();
            }
        }
        E.render();
    }

    function onDblClick(e) {
        e.stopPropagation();
        const hit = maskAwareHit(pointerNorm(e));
        if (hit < 0) return;
        E.select(state.boxes[hit]);
        E.render();
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
            if (e.shiftKey) E.cutoutSelected();
            else E.deleteSelected();
            return;
        }
        if ((e.key === "[" || e.key === "]") && state.primary) {
            e.preventDefault();
            e.stopPropagation();
            E.moveSelectedRegion(e.key === "]" ? 1 : -1);
            return;
        }
        if (mod && key === "c" && state.selection.size) {
            e.preventDefault();
            e.stopPropagation();
            E.copySelection();
            return;
        }
        if (mod && key === "v" && E.clipboardSize()) {
            e.preventDefault();
            e.stopPropagation();
            E.pasteClipboard();
            return;
        }
        // Always swallowed so the browser bookmark dialog never fires.
        if (mod && key === "d") {
            e.preventDefault();
            e.stopPropagation();
            if (state.selection.size) E.pasteRegions(E.selectionInOrder());
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
            E.syncWidget();
            E.render();
            return;
        }
        if (key === "h" && !mod && !e.altKey && !e.shiftKey) {
            e.preventDefault();
            e.stopPropagation();
            state.hideBoxes = !state.hideBoxes;
            E.render();
        }
        if (key === "f" && !mod && !e.altKey && !e.shiftKey) {
            e.preventDefault();
            e.stopPropagation();
            E.onToggleFullscreen();
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
        E.syncWidget();
        E.render();
    }

    function onKindChange() {
        const box = state.primary;
        if (!box) return;
        box.kind = kindSelect.value === "text" ? "text" : "object";
        E.syncWidget();
        E.render();
        if (box.kind === "text") textInput.focus();
    }

    function onTextInput() {
        const box = state.primary;
        if (!box) return;
        box.text = textInput.value;
        E.syncWidget();
        E.render();
    }

    // --- Inspector flow ----------------------------------------------------
    // Repopulate only when the selected region object changes, so the render
    // loop never clobbers live typing or resets the cursor.
    let inspected = null;

    function syncInspector() {
        const box = state.primary;
        const showText = !!box && box.kind === "text";
        textInput.style.display = showText ? "" : "none";
        textInput.disabled = !showText;
        const wired = !!box && E.descWiredFor(box);
        descInput.disabled = !box || wired;
        descInput.placeholder = wired
            ? `wired from the desc_${state.boxes.indexOf(box) + 1} input`
            : "description — e.g. a red vintage car";
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

    Object.assign(E, {
        pointerNorm,
        maskAwareHit,
        onPointerDown,
        onPointerMove,
        onPointerUp,
        onDblClick,
        onKeyDown,
        onInspectorPointerDown,
        onInspectorKeyDown,
        onDescInput,
        onKindChange,
        onTextInput,
        syncInspector,
    });
}
