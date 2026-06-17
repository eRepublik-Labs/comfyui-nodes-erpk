// ABOUTME: Canvas layout and all drawing for the region editor — boxes, masks, ghosts, grid, status.
// ABOUTME: Owns render()/layout(); cross-module state and panels are reached through the injected E.
// @ts-check

import {
    colorForRegion,
    hexToRgba,
    darkenHex,
    clamp,
    rectFrom,
    ratioString,
    fitFrameToImage,
} from "./geometry.js";
import {
    frameAspect,
    frameDims,
    findWidget,
    upstreamImage,
} from "./node_access.js";
import {
    ensureMaskImg,
    ghostCheckerFor,
    cutoutFor,
    checkerPattern,
} from "./masks.js";
import { fmtUsd } from "./scanClient.js";
import { setEyeIcon } from "./styles.js";
import {
    STAGE_PADDING_PX,
    LABEL_FONT,
    HANDLE_DRAW_PX,
    INK_ON_TAPE,
    HAIRLINE,
    HAIRLINE_STRONG,
    ACTIVE_GREEN,
    ACTIVE_GREEN_BORDER,
    DANGER_RED,
} from "./constants.js";

export function installRenderer(E) {
    const { node, state, canvas, stage, statusLeft, statusRight,
            matchBtn, maskBtn, hideBtn, scanBtn, clearBtn } = E;
    const ctx = E.ctx2d;

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
        // Resizing the canvas blanks it; repaint synchronously so a resize never
        // flashes empty for a frame.
        paint();
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

    // A moved region's origin erase-preview (the checkerboard silhouette where
    // it used to be) is a vacated/background area, so it draws backmost — the
    // same lowest-depth rule as cut-outs — and a region moved over it paints on
    // top instead of sliding under it.
    function drawMoveGhost(box) {
        if (box.cutout || !(box.mask && E.regionMoved(box))) return;
        ensureMaskImg(box, render);
        const gx = box.src.x * state.cssW;
        const gy = box.src.y * state.cssH;
        const gw = box.src.w * state.cssW;
        const gh = box.src.h * state.cssH;
        const ghost = ghostCheckerFor(box, gw, gh);
        if (ghost) ctx.drawImage(ghost, gx, gy, gw, gh);
    }

    function drawBox(box, index) {
        if (E.effectiveHidden(box)) return;
        // A cut-out region renders only as the transparency checker behind its
        // mask (or its whole box when maskless) — no box, label, or handles. It
        // reads as "already removed", matching the transparent image output.
        if (box.cutout) {
            const cx = box.x * state.cssW, cy = box.y * state.cssH;
            const cw = box.w * state.cssW, ch = box.h * state.cssH;
            ensureMaskImg(box, render);  // decode the mask so the silhouette survives reload
            const ghost = ghostCheckerFor(box, cw, ch);
            if (ghost) {
                ctx.drawImage(ghost, cx, cy, cw, ch);
            } else {
                ctx.save();
                ctx.fillStyle = checkerPattern(ctx);
                ctx.fillRect(cx, cy, cw, ch);
                ctx.restore();
            }
            return;
        }
        const x = box.x * state.cssW;
        const y = box.y * state.cssH;
        const w = box.w * state.cssW;
        const h = box.h * state.cssH;
        const color = colorForRegion(box, index);
        const isSelected = state.selection.has(box);

        // A moved scanned region previews its relocation: the origin shows an
        // erase-preview (a checkerboard silhouette — "already cut out") and
        // the masked cut-out follows the box ABOVE it, so a small nudge reads
        // as the object sliding off its own hole. Clicking the ghost snaps
        // back; an arrow ties origin to destination.
        if (box.mask && E.regionMoved(box)) {
            ensureMaskImg(box, render);  // decode the mask so the ghost survives reload
            const gx = box.src.x * state.cssW;
            const gy = box.src.y * state.cssH;
            const gw = box.src.w * state.cssW;
            const gh = box.src.h * state.cssH;
            // The origin checkerboard itself is drawn backmost by drawMoveGhost;
            // here only the relocated object, its origin outline, and the arrow.
            const cutout = cutoutFor(box, upstreamImage(node, "image"), render);
            if (cutout) ctx.drawImage(cutout, x, y, w, h);
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
        if (E.descWiredFor(box)) {
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

        // A crosshair at the box center previews the placement dot drawn at
        // execute time, for the elements the model places itself: additions and
        // model-applied moves with their marker on. Node-composited moves and
        // node-inserted refs already have their pixels, and an unmoved scanned
        // region is an anchor — none get a dot, so none get a crosshair.
        const moved = E.regionMoved(box);
        const nodeRefInsert = E.refWiredFor(box) && box.edit_by !== "model";
        const showCrosshair = box.markers !== false && !box.cutout && !nodeRefInsert
            && (moved ? box.edit_by === "model" : box.src == null);
        if (showCrosshair) {
            const cx = x + w / 2;
            const cy = y + h / 2;
            const r = Math.max(3, Math.min(9, Math.min(w, h) * 0.18));
            ctx.save();
            ctx.lineCap = "round";
            ctx.lineWidth = 1.5;
            ctx.strokeStyle = color;
            ctx.globalAlpha = 0.55;
            ctx.beginPath();
            ctx.moveTo(cx - r, cy);
            ctx.lineTo(cx + r, cy);
            ctx.moveTo(cx, cy - r);
            ctx.lineTo(cx, cy + r);
            ctx.stroke();
            ctx.restore();
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
        if (E.descWiredFor(box)) {
            const plugW = Math.ceil(ctx.measureText("⌁").width) + 7;
            ctx.fillStyle = color;
            ctx.fillRect(labelX + 1, y, plugW, 13);
            ctx.fillStyle = ink;
            ctx.fillText("⌁", labelX + 4.5, y + 9.5);
            labelX += plugW + 1;
        }
        if (E.refWiredFor(box)) {
            const chipW = Math.ceil(ctx.measureText("▣").width) + 7;
            ctx.fillStyle = color;
            ctx.fillRect(labelX + 1, y, chipW, 13);
            ctx.fillStyle = ink;
            ctx.fillText("▣", labelX + 4.5, y + 9.5);
            labelX += chipW + 1;
        }
        // A green chip flags a region whose move/cut-out the model applies, not
        // the node — a distinct hue so it reads as a mode flag, not a wired input.
        if (box.edit_by === "model") {
            const chipW = Math.ceil(ctx.measureText("✦").width) + 7;
            ctx.fillStyle = ACTIVE_GREEN;
            ctx.fillRect(labelX + 1, y, chipW, 13);
            ctx.fillStyle = "rgba(8, 8, 10, 0.9)";
            ctx.fillText("✦", labelX + 4.5, y + 9.5);
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
        if (E.refWiredFor(box)) {
            const thumb = upstreamImage(node, `ref_${index + 1}`);
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

    // Draws the upstream image stretched to the frame; a distorted reference
    // is the cue that width/height do not match the source image.
    function drawReference() {
        const img = upstreamImage(node, "image");
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
        const index = E.primaryIndex();
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
        // The last scan's cost, with the running session total once a second
        // scan has added to it. Hidden mid-scan so a stale figure never shows.
        if (state.scanCost && !state.scanning) {
            const cost = document.createElement("span");
            let text = ` · scan ${fmtUsd(state.scanCost.usd)}`;
            if (state.scanSessionUsd > 0 &&
                state.scanSessionUsd !== state.scanCost.usd) {
                text += ` (session ${fmtUsd(state.scanSessionUsd)})`;
            }
            cost.textContent = text;
            cost.style.color = "rgba(255, 255, 255, 0.45)";
            const tokens = (state.scanCost.input_tokens || 0) +
                (state.scanCost.output_tokens || 0);
            cost.title = `${tokens.toLocaleString()} tokens over ` +
                `${state.scanCost.calls || 0} call(s) · ${state.scanCost.model || "?"} ` +
                `· paid-tier estimate (free tier bills nothing)`;
            statusLeft.appendChild(cost);
        }
        const w = Number(findWidget(node, "width")?.value) || 1024;
        const h = Number(findWidget(node, "height")?.value) || 1024;
        statusRight.textContent = `${w}×${h} · ${ratioString(w, h)}`;
        // An edit output follows the source image's canvas, so a frame whose
        // aspect differs from the connected reference composes for a shape
        // that will not exist; the chip offers a one-click match.
        const refImg = upstreamImage(node, "image");
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
        // Restore "flex" (not ""), or the SVG loses floatOnStage's centering —
        // "" reverts the button to its non-flex default display.
        scanBtn.style.display = scanReady ? "flex" : "none";
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
            // Lock the canvas to a busy cursor for the duration of the scan.
            canvas.style.cursor = "wait";
        } else if (!state.scanning && busy) {
            delete scanBtn.dataset.busy;
            scanBtn.textContent = "✦";
            canvas.style.cursor = "crosshair";
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
        if (!count) E.disarmClear();
        E.syncRegionSockets();
        E.syncInspector();
    }

    // Gemini-gradient sweep while the scan runs: an eased ping-pong band in
    // the Gemini brand colors glides over a softly dimmed frame, additively
    // blended so it glows instead of veiling.
    function drawScanSweep() {
        // A section scan sweeps only its host region; a full scan, the frame.
        const b = state.scanBounds;
        const rx = b ? b.x * state.cssW : 0;
        const ry = b ? b.y * state.cssH : 0;
        const rw = b ? b.w * state.cssW : state.cssW;
        const rh = b ? b.h * state.cssH : state.cssH;
        const phase = (performance.now() % 2400) / 2400;
        // Cosine ping-pong: glides to the bottom and back with soft turns.
        const t = (1 - Math.cos(phase * 2 * Math.PI)) / 2;
        const y = ry + t * rh;
        const half = Math.min(80, rh * 0.45);
        ctx.save();
        ctx.beginPath();
        ctx.rect(rx, ry, rw, rh);
        ctx.clip();
        ctx.fillStyle = "rgba(0, 0, 0, 0.18)";
        ctx.fillRect(rx, ry, rw, rh);
        ctx.globalCompositeOperation = "lighter";
        const band = ctx.createLinearGradient(0, y - half, 0, y + half);
        band.addColorStop(0, "rgba(66, 133, 244, 0)");
        band.addColorStop(0.35, "rgba(66, 133, 244, 0.16)");
        band.addColorStop(0.5, "rgba(155, 114, 203, 0.22)");
        band.addColorStop(0.65, "rgba(217, 101, 112, 0.16)");
        band.addColorStop(1, "rgba(217, 101, 112, 0)");
        ctx.fillStyle = band;
        ctx.fillRect(rx, y - half, rw, half * 2);
        // Leading edge: a thin line running the Gemini gradient horizontally.
        const edge = ctx.createLinearGradient(rx, 0, rx + rw, 0);
        edge.addColorStop(0, "rgba(66, 133, 244, 0.75)");
        edge.addColorStop(0.5, "rgba(155, 114, 203, 0.85)");
        edge.addColorStop(1, "rgba(217, 101, 112, 0.75)");
        ctx.fillStyle = edge;
        ctx.fillRect(rx, y - 1, rw, 2);
        ctx.restore();
    }

    // Drives render at animation rate only while a scan is in flight; the
    // loop ends itself on the final post-scan render.
    function scanFxLoop() {
        paint();
        if (state.scanning) requestAnimationFrame(scanFxLoop);
    }

    // Coalesces the many render() calls a single interaction fires (every
    // pointermove, plus the cascade of state mutations) into one paint per
    // animation frame. layout() and scanFxLoop, which must repaint without a
    // frame of latency, call paint() directly instead.
    let framePending = false;
    function render() {
        if (framePending) return;
        framePending = true;
        requestAnimationFrame(() => {
            framePending = false;
            paint();
        });
    }

    function paint() {
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
            // Backmost first: cut-out checkerboards and moved-region origin
            // ghosts are vacated/background areas, so every kept region paints on
            // top of them (matching the output). Each box keeps its real index so
            // colors and labels stay correct.
            state.boxes.forEach((box, i) => { if (box.cutout) drawBox(box, i); });
            state.boxes.forEach((box) => drawMoveGhost(box));
            state.boxes.forEach((box, i) => { if (!box.cutout) drawBox(box, i); });
        }
        if (state.drag?.mode === "create" || state.drag?.mode === "marquee") drawPending();
        if (state.drag?.mode === "resize") drawResizeBadge(state.drag.box);
        if (state.scanning) drawScanSweep();
        renderStatus();
        // Keyboard mutations (delete, paste, duplicate, depth) reach the open
        // panel through the shared render path; a row drag in flight owns the
        // row DOM and must not be rebuilt under the pointer.
        if (E.panel && !E.panelRowDragging) {
            E.renderPanelRows();
            E.refreshPanelDim();
            E.refreshPanelDetail();
        }
    }

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

    Object.assign(E, { layout, render, cornerHandles, scanFxLoop });
}
