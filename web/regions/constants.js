// ABOUTME: Shared constants for the region editor — node id, sizes, colors, fonts, and SVG glyphs.
// ABOUTME: Pure values only so any module (including the pure ones) can import without side effects.

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
export const STATUS_STRIP_H = 22;
export const INSPECTOR_H = 26;
// Vertical chrome around the canvas inside the editor root: panel padding,
// canvas border, the inspector row, the status strip, and the flex gaps.
export const EDITOR_CHROME_V = 70;

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
