// ABOUTME: Pure geometry, color, and frame-math helpers for the region editor.
// ABOUTME: No app, DOM, or shared editor state — every value comes in as an argument.

import { MIN_REGION_SIZE } from "./constants.js";

// Regions cycle through gaffer-tape hues so each keeps a stable identity on
// the stage; kind is marked by the T badge and rendered text, not by color.
export const TAPE_COLORS = ["#4cc9f0", "#f9a826", "#f15bb5", "#9ef01a", "#9b5de5", "#ff6d5a"];

export function regionColor(index) {
    return TAPE_COLORS[index % TAPE_COLORS.length];
}

// Deterministic small hash so a class label always maps to the same hue.
export function hashString(str) {
    let h = 0;
    for (let i = 0; i < str.length; i++) {
        h = (h * 31 + str.charCodeAt(i)) | 0;
    }
    return h;
}

// Scanned regions carry a class label in box.group; same-label regions share a
// hue so the object layer reads as classes. Hand-drawn regions keep their
// index-cycled identity color.
export function colorForRegion(box, index) {
    if (box.group) {
        return TAPE_COLORS[Math.abs(hashString(box.group)) % TAPE_COLORS.length];
    }
    return regionColor(index);
}

export function clamp(v, lo, hi) {
    return Math.min(Math.max(v, lo), hi);
}

export function round4(v) {
    return Math.round(v * 10000) / 10000;
}

export function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// Glyph ink on a tape chip: the chip's own hue scaled toward black reads as
// a shade of the region color instead of a foreign white or black.
export function darkenHex(hex, factor) {
    const r = Math.round(parseInt(hex.slice(1, 3), 16) * factor);
    const g = Math.round(parseInt(hex.slice(3, 5), 16) * factor);
    const b = Math.round(parseInt(hex.slice(5, 7), 16) * factor);
    return `rgb(${r}, ${g}, ${b})`;
}

// Axis-aligned rect from two corner points (both already clamped to the unit
// square), normalizing inverted drags into positive width/height.
export function rectFrom(a, b) {
    return {
        x: Math.min(a.x, b.x),
        y: Math.min(a.y, b.y),
        w: Math.abs(a.x - b.x),
        h: Math.abs(a.y - b.y),
    };
}

export function enforceMinSize(box) {
    box.w = Math.max(box.w, MIN_REGION_SIZE);
    box.h = Math.max(box.h, MIN_REGION_SIZE);
    box.x = clamp(box.x, 0, 1 - box.w);
    box.y = clamp(box.y, 0, 1 - box.h);
}

export function ratioString(w, h) {
    const gcd = (a, b) => (b ? gcd(b, a % b) : a);
    const d = gcd(w, h) || 1;
    return `${Math.round(w / d)}:${Math.round(h / d)}`;
}

// Frame dimensions matching an image's aspect, scaled into the widget
// range and snapped to the widgets' step of 8.
export function fitFrameToImage(iw, ih) {
    const down = Math.min(8192 / iw, 8192 / ih, 1);
    const up = Math.max(64 / (iw * down), 64 / (ih * down), 1);
    const w = Math.round((iw * down * up) / 8) * 8;
    const h = Math.round((ih * down * up) / 8) * 8;
    return { w: clamp(w, 64, 8192), h: clamp(h, 64, 8192) };
}
