// ABOUTME: DOM styling helpers for the region editor — button/input styling and the eye icon.
// ABOUTME: Importing this injects the editor's hover/animation stylesheet once into the document head.
// @ts-check

import { DANGER_RED, PANEL_INPUT_BG, EYE_SVG, EYE_OFF_SVG } from "./constants.js";

// Hover states need real CSS pseudo-classes; !important outweighs the inline
// base styles the elements carry. The danger rule comes last so it wins over
// the generic button rule on the red controls.
const hoverStyles = document.createElement("style");
hoverStyles.textContent = `
.erpk-region-row { transition: background 130ms cubic-bezier(0.16, 1, 0.3, 1); }
.erpk-region-row:hover { background: rgba(255, 255, 255, 0.05); }
.erpk-region-row-selected { background: rgba(82, 201, 125, 0.10); }
.erpk-region-row-selected:hover { background: rgba(82, 201, 125, 0.14); }
/* Per-row tools stay out of the way until the row is hovered or one is focused;
   the eye (most-used) stays but dimmed. Keeps the list a quiet stack at rest. */
.erpk-row-tool {
    opacity: 0;
    transition: opacity 130ms cubic-bezier(0.16, 1, 0.3, 1);
}
.erpk-region-row:hover .erpk-row-tool,
.erpk-row-tool:focus-visible { opacity: 1; }
.erpk-row-eye { opacity: 0.4; transition: opacity 130ms cubic-bezier(0.16, 1, 0.3, 1); }
.erpk-region-row:hover .erpk-row-eye,
.erpk-row-eye:focus-visible { opacity: 0.9; }
@media (prefers-reduced-motion: reduce) {
    .erpk-region-row, .erpk-row-tool, .erpk-row-eye { transition: none; }
    .erpk-row-tool { opacity: 1; }
}
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
@keyframes erpk-gemini-shimmer { to { background-position: -200% center; } }
.erpk-scan-text {
    background: linear-gradient(90deg,
        #4285f4, #9b72cb, #d96570, #9b72cb, #4285f4);
    background-size: 200% auto;
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    animation: erpk-gemini-shimmer 2.4s linear infinite;
}
.erpk-stage-btn { opacity: 0.6; }
.erpk-stage-btn:hover:not(:disabled),
.erpk-stage-btn[data-busy="1"],
.erpk-stage-btn.erpk-btn-active {
    opacity: 1 !important;
}
`;
document.head.appendChild(hoverStyles);

export function setEyeIcon(btn, hidden) {
    btn.innerHTML = hidden ? EYE_OFF_SVG : EYE_SVG;
}

export function makeStripButton(label) {
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

// Give icon-only controls an accessible name for screen readers by mirroring
// their tooltip text (data-tip) onto aria-label. The visible label is a glyph,
// which announces as nothing useful, so without this the controls are unlabeled.
// Run after a subtree's tips are set; it skips controls already named.
export function labelControlsFromTips(scope) {
    for (const el of scope.querySelectorAll("[data-tip]")) {
        if (!el.getAttribute("aria-label") && el.dataset.tip) {
            el.setAttribute("aria-label", el.dataset.tip);
        }
    }
}

// A fixed square icon button: one width/height for the whole toolbar so the
// controls form an even row. The caller supplies the SVG via innerHTML.
export function sizeIconButton(btn, px = 24) {
    btn.style.width = px + "px";
    btn.style.height = px + "px";
    btn.style.minWidth = px + "px";
    btn.style.padding = "0";
    btn.style.boxSizing = "border-box";
    btn.style.display = "inline-flex";
    btn.style.alignItems = "center";
    btn.style.justifyContent = "center";
    return btn;
}

// Inspector controls sit in the stage's color world rather than following
// the UI theme, matching the canvas and status strip around them.
export function styleInput(el) {
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
