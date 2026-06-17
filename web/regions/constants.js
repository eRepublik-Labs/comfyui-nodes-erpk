// ABOUTME: Shared constants for the region editor — node id, sizes, colors, fonts, and SVG glyphs.
// ABOUTME: Pure values only so any module (including the pure ones) can import without side effects.
// @ts-check

export const NODE_ID = "RegionalPromptBuilder";
export const MIN_REGION_SIZE = 0.01;   // normalized floor; Python skips regions at or below 0.005
export const HANDLE_HIT_PX = 7;
export const HANDLE_DRAW_PX = 6;
export const STAGE_PADDING_PX = 0;
export const LABEL_FONT = "11px 'Segoe UI', sans-serif";
export const MIN_NODE_WIDTH = 340;
// Per-side inset ComfyUI applies between the outer node frame and the inner
// widget area; the DOM widget wrapper is wider than the usable area without it.
export const CHROME_HORIZONTAL_INSET = 16;
// Absolute floor for degenerate aspect ratios; otherwise the canvas height
// follows the frame aspect exactly so the canvas always spans the full width.
export const CANVAS_MIN_H = 60;
// Matches DESC_INPUT_COUNT / REF_INPUT_COUNT on the Python side.
export const REGION_DESC_INPUTS = 10;
export const REGION_REF_INPUTS = 10;
// Upper bound the vision scan asks the engine for; mirrors the route default.
export const SCAN_MAX_OBJECTS = 20;
export const SCAN_MAX_EDGE_PX = 1536;

// Grid cell size is expressed in frame pixels, so the grid quantizes to the
// generated image's own pixel space (64 aligns with latent blocks).
export const GRID_MIN_CELL_PX = 8;
export const GRID_MAX_CELL_PX = 1024;
export const GRID_DEFAULT_CELL_PX = 64;
export const GRID_DEFAULT_COLOR = "#26262e";
// Active/toggled-on state for strip and inspector controls.
export const ACTIVE_GREEN = "#52c97d";
export const ACTIVE_GREEN_BORDER = "rgba(82, 201, 125, 0.55)";
// Destructive-action red for the clear-all control.
export const DANGER_RED = "#e5484d";
export const DANGER_RED_DIM = "rgba(229, 72, 77, 0.85)";
export const DANGER_RED_BORDER = "rgba(229, 72, 77, 0.40)";

// Horizontal padding the editor root carries inside the DOM widget wrapper.
export const ROOT_PADDING_H = 12;
export const STATUS_STRIP_H = 28;
export const INSPECTOR_H = 28;
// Vertical chrome around the canvas inside the editor root: panel padding,
// canvas border, the inspector row, the status strip, and the flex gaps.
export const EDITOR_CHROME_V = 70;

// Fixed height for the multiline scene-prompt field. Capping it (instead of
// letting it absorb the node's slack) keeps the node's minimum height small, so
// it defaults compact, can be shrunk, and stays put on reload; the field scrolls
// for longer text. ~4 rows plus the widget's own chrome.
export const PROMPT_FIELD_H = 96;

// The canvas is a stage for the image-to-be: dark like every ComfyUI content
// preview, independent of the UI theme. Chrome around it follows the theme.
export const STAGE_BG = "#101014";
export const PANEL_BG = "#16161c";
export const PANEL_INPUT_BG = "#0d0d12";
export const HAIRLINE = "rgba(255, 255, 255, 0.10)";
export const HAIRLINE_STRONG = "rgba(255, 255, 255, 0.25)";
export const INK_ON_TAPE = "#0b0b0e";

// Visibility toggles render a real eye: open when shown, struck when hidden.
export const EYE_SVG =
    '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" '
    + 'stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
    + 'stroke-linejoin="round" style="display:block">'
    + '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/>'
    + '<circle cx="12" cy="12" r="3"/></svg>';
export const EYE_OFF_SVG =
    '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" '
    + 'stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
    + 'stroke-linejoin="round" style="display:block">'
    + '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/>'
    + '<circle cx="12" cy="12" r="3"/>'
    + '<line x1="4" y1="20" x2="20" y2="4"/></svg>';

// Picture glyph for the reference-image socket toggle.
export const IMAGE_SVG =
    '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" '
    + 'stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
    + 'stroke-linejoin="round" style="display:block">'
    + '<rect x="3" y="3" width="18" height="18" rx="2"/>'
    + '<circle cx="8.5" cy="8.5" r="1.6"/>'
    + '<path d="M21 15l-5-5L5 21"/></svg>';

export const TRASH_SVG =
    '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" '
    + 'stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
    + 'stroke-linejoin="round" style="display:block">'
    + '<path d="M3 6h18"/>'
    + '<path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>'
    + '<path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>'
    + '<path d="M10 11v6M14 11v6"/></svg>';

// Lucide icons (MIT-licensed, lucide.dev) inlined as one coherent stroke set —
// no build step or runtime dependency, and currentColor lets each icon inherit
// its button's hover/active color. Same wrapper metric as the icons above so the
// whole editor draws from a single family.
function lucide(inner) {
    return '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" '
        + 'stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
        + 'stroke-linejoin="round" style="display:block">' + inner + "</svg>";
}

export const CONTRAST_SVG =
    lucide('<circle cx="12" cy="12" r="10"/><path d="M12 18a6 6 0 0 0 0-12z"/>');
export const GRID_SVG =
    lucide('<rect width="18" height="18" x="3" y="3" rx="2"/>'
        + '<path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>');
export const CROSSHAIR_SVG =
    lucide('<circle cx="12" cy="12" r="10"/>'
        + '<path d="M22 12h-4M6 12H2M12 6V2M12 22v-4"/>');
export const HELP_SVG =
    lucide('<circle cx="12" cy="12" r="10"/>'
        + '<path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>');
export const SETTINGS_SVG =
    lucide('<path d="M20 7h-9"/><path d="M14 17H5"/>'
        + '<circle cx="17" cy="17" r="3"/><circle cx="7" cy="7" r="3"/>');
// Lucide "sparkle" (singular) — one clean 4-point star, simpler than the full
// "sparkles" at small sizes.
export const SPARKLES_SVG =
    lucide('<path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0'
        + '-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0'
        + 'L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964'
        + 'L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/>');
export const LINK_SVG =
    lucide('<path d="M9 17H7A5 5 0 0 1 7 7h2"/>'
        + '<path d="M15 7h2a5 5 0 1 1 0 10h-2"/><line x1="8" x2="16" y1="12" y2="12"/>');
export const MAXIMIZE_SVG =
    lucide('<path d="M8 3H5a2 2 0 0 0-2 2v3M21 8V5a2 2 0 0 0-2-2h-3'
        + 'M3 16v3a2 2 0 0 0 2 2h3M16 21h3a2 2 0 0 0 2-2v-3"/>');
export const MINIMIZE_SVG =
    lucide('<path d="M8 3v3a2 2 0 0 1-2 2H3M21 8h-3a2 2 0 0 1-2-2V3'
        + 'M3 16h3a2 2 0 0 1 2 2v3M16 21v-3a2 2 0 0 1 2-2h3"/>');
export const CHEVRON_DOWN_SVG = lucide('<path d="m6 9 6 6 6-6"/>');
export const CHEVRON_UP_SVG = lucide('<path d="m18 15-6-6-6 6"/>');
export const COPY_SVG =
    lucide('<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/>'
        + '<path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>');
