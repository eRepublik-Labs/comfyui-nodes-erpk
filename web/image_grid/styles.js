// ABOUTME: Layout constants and the stylesheet for the image grid widget.
// ABOUTME: The node height arithmetic and the CSS read the same numbers, so they cannot drift.
// @ts-check

import {
    ACTIVE_GREEN,
    ACTIVE_GREEN_BORDER,
    DANGER_RED,
    DANGER_RED_BORDER,
    PANEL_BG,
    PANEL_INPUT_BG,
} from "../regions/constants.js";

export const COLUMNS = 4;
export const GAP = 8;
export const ZONE_PAD = 10;
export const ZONE_BORDER = 1;
export const EMPTY_H = 150;
export const FOOTER_GAP = 10;
export const FOOTER_H = 26;
export const NOTICE_H = 24;
export const HEADER_H = 24;
export const HEADER_GAP = 8;
export const ROOT_PAD_TOP = 0;
export const ROOT_PAD_BOTTOM = 4;
// The frontend wraps a DOM widget in 10px top and bottom margins and sizes the
// element to the declared height minus those margins (measured, frontend 1.57.6),
// so the declared height must carry them or the zone overflows the root.
export const DOM_WIDGET_MARGIN_V = 20;
export const ROOT_PAD_V = ROOT_PAD_TOP + ROOT_PAD_BOTTOM + DOM_WIDGET_MARGIN_V;
export const MIN_NODE_WIDTH = 300;

const TAG_H = 18;
const LINE = "#2a2a33";
const LINE_SOFT = "#1f1f27";
const TEXT = "#d6d6de";
const MUTED = "#8b8b98";
const CELL_BG = "#1b1b22";
export const TITLE_COUNT_COLOR = MUTED;
export const TITLE_COUNT_FULL_COLOR = DANGER_RED;

const sheet = document.createElement("style");
sheet.textContent = `
.erpk-grid-root {
    box-sizing: border-box;
    padding: ${ROOT_PAD_TOP}px 0 ${ROOT_PAD_BOTTOM}px;
    color: ${TEXT};
    font: 12px/1.4 'Segoe UI', system-ui, sans-serif;
    touch-action: manipulation;
    -webkit-tap-highlight-color: transparent;
}
.erpk-grid-root *, .erpk-grid-root *::before { box-sizing: border-box; }
/* Component rules set display, which would otherwise override the hidden attribute. */
.erpk-grid-root [hidden] { display: none !important; }
.erpk-grid-zone {
    position: relative;
    padding: ${ZONE_PAD}px;
    border: ${ZONE_BORDER}px dashed ${LINE};
    border-radius: 6px;
    background: ${PANEL_INPUT_BG};
}
.erpk-grid-zone.erpk-grid-over { border-style: solid; border-color: ${ACTIVE_GREEN}; background: #0f1713; }
.erpk-grid-zone.erpk-grid-over.erpk-grid-refuse { border-color: ${DANGER_RED}; background: #170f10; }
.erpk-grid-zone.erpk-grid-over .erpk-grid-list { opacity: 0.35; }
.erpk-grid-zone.erpk-grid-ignored { opacity: 0.5; cursor: default; }
.erpk-grid-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    height: ${HEADER_H}px;
}
.erpk-grid-zone:not(.erpk-grid-collapsed) .erpk-grid-header { margin-bottom: ${HEADER_GAP}px; }
.erpk-grid-toggle {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    height: ${HEADER_H}px;
    min-width: 0;
    padding: 0 6px 0 2px;
    border: none;
    border-radius: 4px;
    background: transparent;
    color: ${TEXT};
    font: inherit;
    font-weight: 600;
    white-space: nowrap;
    cursor: pointer;
}
.erpk-grid-toggle:hover { color: #fff; }
.erpk-grid-chevron { width: 12px; color: ${MUTED}; font-size: 18px; line-height: 1; text-align: center; }
.erpk-grid-toggle:hover .erpk-grid-chevron { color: ${TEXT}; }
.erpk-grid-header-count { color: ${MUTED}; font-size: 11px; font-variant-numeric: tabular-nums; white-space: nowrap; }
.erpk-grid-list {
    display: grid;
    grid-template-columns: repeat(${COLUMNS}, minmax(0, 1fr));
    gap: ${GAP}px;
    margin: 0;
    padding: 0;
    list-style: none;
}
.erpk-grid-root.erpk-grid-reordering { user-select: none; -webkit-user-select: none; }
.erpk-grid-cell {
    position: relative;
    aspect-ratio: 1;
    border-radius: 4px;
    background: ${CELL_BG};
    border: 1px solid ${LINE_SOFT};
    cursor: grab;
}
.erpk-grid-cell > img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
    border-radius: 3px;
    pointer-events: none;
}
.erpk-grid-cell:focus-visible, .erpk-grid-btn:focus-visible, .erpk-grid-remove:focus-visible, .erpk-grid-toggle:focus-visible {
    outline: 2px solid ${ACTIVE_GREEN};
    outline-offset: 2px;
}
.erpk-grid-cell.erpk-grid-dragging { outline: 2px solid ${ACTIVE_GREEN}; outline-offset: -2px; opacity: 0.85; }
.erpk-grid-cell.erpk-grid-insert-before::before,
.erpk-grid-cell.erpk-grid-insert-after::before {
    content: "";
    position: absolute;
    top: 0;
    bottom: 0;
    width: 3px;
    border-radius: 2px;
    background: ${ACTIVE_GREEN};
}
.erpk-grid-cell.erpk-grid-insert-before::before { left: -${GAP / 2 + 2}px; }
.erpk-grid-cell.erpk-grid-insert-after::before { right: -${GAP / 2 + 2}px; }
.erpk-grid-missing {
    position: absolute;
    inset: 0;
    display: none;
    align-items: center;
    justify-content: center;
    color: ${DANGER_RED};
    font-size: 11px;
}
.erpk-grid-is-missing > img { visibility: hidden; }
.erpk-grid-cell.erpk-grid-pending { cursor: default; }
.erpk-grid-cell.erpk-grid-uploading { background: ${LINE}; }
.erpk-grid-spinner {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 18px;
    height: 18px;
    margin: -9px 0 0 -9px;
    border: 2px solid #3a3a46;
    border-top-color: ${TEXT};
    border-radius: 50%;
    animation: erpk-grid-spin 800ms linear infinite;
}
@keyframes erpk-grid-spin { to { transform: rotate(360deg); } }
.erpk-grid-is-missing > .erpk-grid-missing { display: flex; }
/* Corner tags: the outer corner matches the image's 3px radius inside the cell's 1px border. */
.erpk-grid-badge, .erpk-grid-remove {
    position: absolute;
    top: 0;
    height: ${TAG_H}px;
    border: none;
    background: rgba(13, 13, 18, 0.85);
    color: ${TEXT};
    font-size: 11px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.erpk-grid-badge {
    left: 0;
    min-width: ${TAG_H}px;
    padding: 0 5px;
    border-radius: 3px 0 4px 0;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    pointer-events: none;
}
.erpk-grid-remove {
    right: 0;
    width: ${TAG_H}px;
    padding: 0;
    border-radius: 0 3px 0 4px;
    cursor: pointer;
    font-size: 14px;
    line-height: 1;
    opacity: 0;
    transition: opacity 130ms, color 130ms, background-color 130ms;
}
.erpk-grid-cell:hover .erpk-grid-remove,
.erpk-grid-cell:focus-within .erpk-grid-remove,
.erpk-grid-cell:focus-visible .erpk-grid-remove { opacity: 1; }
/* Touch has no hover to reveal it. */
@media (hover: none) { .erpk-grid-remove { opacity: 1; } }
/* The tag is ${TAG_H}px; the hit area grows into the cell to 24px, as there is no room past the corner. */
.erpk-grid-remove::before { content: ""; position: absolute; inset: 0 0 -${24 - TAG_H}px -${24 - TAG_H}px; }
.erpk-grid-remove:hover, .erpk-grid-remove:focus-visible {
    color: #fff;
    background: ${DANGER_RED};
}
.erpk-grid-add {
    aspect-ratio: 1;
    width: 100%;
    border: 1px dashed ${LINE};
    border-radius: 4px;
    background: transparent;
    color: ${MUTED};
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
    font: inherit;
    font-size: 11px;
    cursor: pointer;
}
.erpk-grid-add .erpk-grid-plus { font-size: 22px; line-height: 1; color: ${TEXT}; }
.erpk-grid-add:hover:not(:disabled) { border-color: ${ACTIVE_GREEN_BORDER}; color: ${TEXT}; }
.erpk-grid-add:disabled { cursor: default; }
.erpk-grid-empty {
    min-height: ${EMPTY_H - 2 * ZONE_PAD - 2 * ZONE_BORDER}px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
    color: ${MUTED};
    text-align: center;
}
.erpk-grid-empty .erpk-grid-icon { font-size: 26px; line-height: 1; color: ${TEXT}; }
.erpk-grid-empty .erpk-grid-primary { color: ${TEXT}; font-weight: 500; }
.erpk-grid-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    height: 26px;
    padding: 0 12px;
    border-radius: 13px;
    border: 1px solid ${LINE};
    background: ${PANEL_BG};
    color: ${TEXT};
    font: inherit;
    cursor: pointer;
}
.erpk-grid-btn:hover:not(:disabled) { border-color: ${ACTIVE_GREEN_BORDER}; }
.erpk-grid-btn:disabled { opacity: 0.5; cursor: default; }
.erpk-grid-btn.erpk-grid-ghost { background: transparent; }
.erpk-grid-btn.erpk-grid-ghost:hover:not(:disabled) { border-color: ${DANGER_RED_BORDER}; color: ${DANGER_RED}; }
.erpk-grid-empty .erpk-grid-btn { margin-top: 6px; }
.erpk-grid-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    height: ${FOOTER_H}px;
    margin-top: ${FOOTER_GAP}px;
    color: ${MUTED};
    font-size: 11px;
}
.erpk-grid-capacity { font-variant-numeric: tabular-nums; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.erpk-grid-root .erpk-grid-over-cap { color: ${DANGER_RED}; }
.erpk-grid-overlay {
    position: absolute;
    inset: 0;
    display: none;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 4px;
    padding: 12px;
    border-radius: 5px;
    background: rgba(16, 23, 19, 0.88);
    color: ${ACTIVE_GREEN};
    font-weight: 600;
    text-align: center;
    pointer-events: none;
}
.erpk-grid-over .erpk-grid-overlay { display: flex; }
.erpk-grid-refuse .erpk-grid-overlay { background: rgba(23, 15, 16, 0.9); color: ${DANGER_RED}; }
.erpk-grid-overlay small { color: ${TEXT}; font-weight: 400; font-size: 11px; }
/* A collapsed zone is one header tall, room for the title line only, which would sit on the header's text. */
.erpk-grid-collapsed .erpk-grid-overlay { padding: 0 12px; }
.erpk-grid-collapsed.erpk-grid-over .erpk-grid-header { opacity: 0; }
.erpk-grid-collapsed .erpk-grid-overlay small { display: none; }
.erpk-grid-notice {
    display: flex;
    align-items: center;
    gap: 8px;
    height: ${NOTICE_H}px;
    padding-top: 6px;
    color: ${MUTED};
    font-size: 11px;
}
.erpk-grid-notice-text { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.erpk-grid-notice.erpk-grid-error .erpk-grid-notice-text { color: ${DANGER_RED}; }
.erpk-grid-link {
    flex: none;
    min-height: 24px;
    padding: 0 6px;
    border: none;
    background: transparent;
    color: ${ACTIVE_GREEN};
    font: inherit;
    text-decoration: underline;
    cursor: pointer;
}
.erpk-grid-link:focus-visible { outline: 2px solid ${ACTIVE_GREEN}; outline-offset: 1px; border-radius: 3px; }
.erpk-grid-sr {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
}
@media (prefers-reduced-motion: reduce) {
    .erpk-grid-remove { transition: none; }
    .erpk-grid-spinner { animation: none; }
}
`;
document.head.appendChild(sheet);
