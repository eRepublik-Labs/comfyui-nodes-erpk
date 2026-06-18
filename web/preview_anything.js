// ABOUTME: Frontend renderer for ERPK_PreviewAnything — handles image, video, audio, gif, text, markdown.
// ABOUTME: Adds a download button that saves the rendered content to the user's computer.

import { app } from "../../../scripts/app.js";

const NODE_ID = "ERPK_PreviewAnything";

const EXT_FOR_KIND = {
    text: ".txt",
    markdown: ".md",
    image: ".png",
    gif: ".gif",
    video: ".mp4",
    audio: ".wav",
};

// Inject scoped styles once so the Download button's label stays readable
// across ComfyUI themes and hover states. Using dedicated classes plus
// !important — appended to <head> after theme CSS so source order wins on
// equal-specificity ties.
const STYLE_ID = "erpk-preview-anything-styles";
function ensureStyles() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = `
        .erpk-download-btn,
        .erpk-download-btn:hover,
        .erpk-download-btn:focus,
        .erpk-download-btn:active {
            background: #22c55e !important;
            border: 1px solid #16a34a !important;
            color: #0a0a0a !important;
            text-shadow: none !important;
            box-shadow: none !important;
        }
        .erpk-download-btn:hover:not(:disabled) {
            background: #16a34a !important;
        }
        .erpk-download-btn:disabled,
        .erpk-download-btn:disabled:hover {
            background: #2a3a2f !important;
            border-color: #2e3d33 !important;
            color: #8a8a8a !important;
            cursor: not-allowed !important;
        }
        .erpk-download-btn .erpk-download-label,
        .erpk-download-btn:hover .erpk-download-label,
        .erpk-download-btn:focus .erpk-download-label,
        .erpk-download-btn:active .erpk-download-label {
            color: #0a0a0a !important;
            text-shadow: none !important;
            font-weight: 700 !important;
            font-size: 13px !important;
            letter-spacing: 0.02em !important;
        }
        .erpk-download-btn:disabled .erpk-download-label,
        .erpk-download-btn:disabled:hover .erpk-download-label {
            color: #8a8a8a !important;
        }
        .erpk-copy-btn,
        .erpk-copy-btn:hover,
        .erpk-copy-btn:focus,
        .erpk-copy-btn:active {
            background: #334155 !important;
            border: 1px solid #475569 !important;
            color: #e2e8f0 !important;
            text-shadow: none !important;
            box-shadow: none !important;
        }
        .erpk-copy-btn:hover:not(:disabled) {
            background: #475569 !important;
        }
        .erpk-copy-btn:disabled,
        .erpk-copy-btn:disabled:hover {
            background: #1e293b !important;
            border-color: #334155 !important;
            color: #64748b !important;
            cursor: not-allowed !important;
        }
        .erpk-copy-btn .erpk-copy-label,
        .erpk-copy-btn:hover .erpk-copy-label,
        .erpk-copy-btn:focus .erpk-copy-label,
        .erpk-copy-btn:active .erpk-copy-label {
            color: #e2e8f0 !important;
            text-shadow: none !important;
            font-weight: 700 !important;
            font-size: 13px !important;
            letter-spacing: 0.02em !important;
        }
        .erpk-char-count {
            font-size: 11px !important;
            color: var(--input-text, #888) !important;
            padding: 0 6px !important;
            align-self: center !important;
            font-variant-numeric: tabular-nums !important;
        }
        .erpk-gallery-cell {
            transition: transform 120ms ease, box-shadow 120ms ease, border-color 120ms ease !important;
        }
        .erpk-gallery-cell:hover {
            transform: scale(1.03) !important;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.55) !important;
            border-color: var(--p-primary-color, #5a9dff) !important;
            z-index: 1 !important;
        }
        .erpk-gallery-nav-btn {
            position: absolute !important;
            top: 50% !important;
            transform: translateY(-50%) !important;
            width: 36px !important;
            height: 54px !important;
            background: rgba(0, 0, 0, 0.7) !important;
            color: #fff !important;
            border: 1px solid rgba(255, 255, 255, 0.18) !important;
            border-radius: 4px !important;
            cursor: pointer !important;
            font-size: 22px !important;
            line-height: 1 !important;
            font-weight: 700 !important;
            padding: 0 !important;
            z-index: 3 !important;
            transition: background 120ms ease !important;
        }
        .erpk-gallery-nav-btn:hover:not(:disabled) {
            background: rgba(0, 0, 0, 0.92) !important;
        }
        .erpk-gallery-nav-btn:disabled {
            opacity: 0.3 !important;
            cursor: not-allowed !important;
        }
        /* Dark surfaces mirror the Regional Prompt Builder palette
           (web/regions/constants.js: STAGE_BG/PANEL_BG/PANEL_INPUT_BG) so the
           two nodes read as the same near-black, not pure black. */
        .erpk-preview-anything {
            --erpk-pa-stage: #101014;
            --erpk-pa-panel: #16161c;
            --erpk-pa-input: #0d0d12;
            --erpk-pa-line: rgba(255, 255, 255, 0.08);
            --erpk-pa-text: #e6e6ea;
            --erpk-pa-muted: #8a8a93;
            --erpk-pa-accent: #5a9dff;
        }
        .erpk-pa-optbar {
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
            padding: 7px 10px !important;
            background: var(--erpk-pa-panel) !important;
            border: 1px solid var(--erpk-pa-line) !important;
            border-radius: 8px !important;
            color: var(--erpk-pa-muted) !important;
            cursor: pointer !important;
            font-size: 12px !important;
            font-weight: 600 !important;
            letter-spacing: 0.02em !important;
            user-select: none !important;
            transition: background 140ms ease, color 140ms ease, border-color 140ms ease !important;
        }
        .erpk-pa-optbar:hover {
            background: #1b1b20 !important;
            color: var(--erpk-pa-text) !important;
            border-color: rgba(255, 255, 255, 0.14) !important;
        }
        .erpk-pa-optbar .erpk-pa-chevron {
            margin-left: auto !important;
            font-size: 10px !important;
            opacity: 0.7 !important;
            transition: transform 180ms cubic-bezier(0.16, 1, 0.3, 1) !important;
        }
        .erpk-pa-optpanel {
            display: flex;
            flex-direction: column;
            gap: 9px;
            padding: 11px;
            background: var(--erpk-pa-panel);
            border: 1px solid var(--erpk-pa-line);
            border-radius: 8px;
        }
        .erpk-pa-field {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .erpk-pa-flabel {
            flex: 0 0 86px;
            font-size: 11px;
            font-weight: 600;
            color: var(--erpk-pa-muted);
            letter-spacing: 0.02em;
        }
        .erpk-pa-input,
        .erpk-pa-select {
            flex: 1 1 auto;
            min-width: 0;
            background: var(--erpk-pa-input, #0d0d12) !important;
            color: var(--erpk-pa-text) !important;
            border: 1px solid var(--erpk-pa-line) !important;
            border-radius: 6px !important;
            padding: 6px 8px !important;
            font-size: 12px !important;
            outline: none !important;
            box-shadow: none !important;
            transition: border-color 140ms ease, box-shadow 140ms ease !important;
        }
        .erpk-pa-input:focus,
        .erpk-pa-select:focus {
            border-color: var(--erpk-pa-accent) !important;
            box-shadow: 0 0 0 2px rgba(90, 157, 255, 0.18) !important;
        }
        .erpk-pa-switch {
            position: relative !important;
            flex: 0 0 auto !important;
            width: 38px !important;
            height: 22px !important;
            border-radius: 999px !important;
            background: #2a2a30 !important;
            border: 1px solid var(--erpk-pa-line) !important;
            cursor: pointer !important;
            padding: 0 !important;
            transition: background 160ms ease, border-color 160ms ease !important;
        }
        .erpk-pa-switch[aria-checked="true"] {
            background: var(--erpk-pa-accent) !important;
            border-color: var(--erpk-pa-accent) !important;
        }
        .erpk-pa-knob {
            position: absolute;
            top: 2px;
            left: 2px;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: #fff;
            transition: transform 160ms cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .erpk-pa-switch[aria-checked="true"] .erpk-pa-knob {
            transform: translateX(16px);
        }
        .erpk-pa-empty {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
            width: 100%;
            color: var(--erpk-pa-muted);
            font-size: 12px;
            text-align: center;
            padding: 16px;
            box-sizing: border-box;
        }
        @media (prefers-reduced-motion: reduce) {
            .erpk-pa-optbar,
            .erpk-pa-chevron,
            .erpk-pa-input,
            .erpk-pa-select,
            .erpk-pa-switch,
            .erpk-pa-knob,
            .erpk-gallery-cell {
                transition: none !important;
            }
        }
    `;
    document.head.appendChild(style);
}

// Display-type options mirror the Combo widget declared in the Python schema
// (utils/preview_anything.py). Kept in sync so the DOM <select> shows the same
// choices the hidden canvas widget serializes.
const DISPLAY_TYPES = ["auto", "text", "markdown", "image", "gif", "video", "audio"];

const EMPTY_TEXT = "No content yet — queue the workflow to preview.";

// Approximate rendered height of the expanded Options panel (three rows +
// padding). Used to grow/shrink the node when the user toggles Options so the
// preview area below keeps its size instead of being squeezed.
const OPTIONS_PANEL_HEIGHT = 132;

const MIN_NODE_HEIGHT = 260;

// Hide a canvas widget while keeping it in node.widgets so its value still
// serializes (widgets_values is positional) and is read at queue time.
// Different widget renderers check different flags: combo/string honor
// type="hidden", while the boolean/toggle renderer keys off widget.hidden /
// options.hidden (the idiom in web/concat_strings.js). Set all of them so the
// hide is widget-type-agnostic. Idempotent: the originals are stashed once.
function hideConfigWidget(widget) {
    if (!widget) return;
    if (widget._erpkOrigType === undefined) {
        widget._erpkOrigType = widget.type;
        widget._erpkOrigComputeSize = widget.computeSize;
    }
    widget.type = "hidden";
    widget.hidden = true;
    if (widget.options) widget.options.hidden = true;
    widget.computeSize = () => [0, -4];
}

const CONFIG_WIDGET_NAMES = ["display_type", "filename", "strip_metadata"];

function findWidget(node, name) {
    return node.widgets?.find((w) => w.name === name) || null;
}

// Hide all three config widgets; returns true once every one was found and
// hidden. V3 nodes can attach a widget a tick after onNodeCreated, so callers
// retry until this reports done.
function hideConfigWidgets(node) {
    let allFound = true;
    for (const name of CONFIG_WIDGET_NAMES) {
        const w = findWidget(node, name);
        if (w) hideConfigWidget(w);
        else allFound = false;
    }
    return allFound;
}

// Mirror the hidden widgets' current values into the DOM Options controls.
// Needed after onConfigure restores widgets_values (which lands after
// onNodeCreated), so the styled controls reflect the loaded workflow.
function syncOptionControls(node) {
    const p = node._erpkPreview;
    if (!p) return;
    const dt = findWidget(node, "display_type");
    const fn = findWidget(node, "filename");
    const sm = findWidget(node, "strip_metadata");
    if (dt && p.selDisplay) p.selDisplay.value = dt.value ?? "auto";
    if (fn && p.inpFilename) p.inpFilename.value = fn.value ?? "preview";
    if (sm && p.swStrip) p.swStrip.setAttribute("aria-checked", String(!!sm.value));
}

// Expand/collapse the Options panel. On a user toggle (adjustSize=true) the
// node grows/shrinks by the panel height so the preview area keeps its size.
// On restore from a saved workflow (adjustSize=false) the node.size already
// reflects the saved state, so we only set visibility.
function setOptionsOpen(node, open, adjustSize) {
    const p = node._erpkPreview;
    if (!p) return;
    const was = !!p.optionsOpen;
    p.optionsOpen = open;
    p.optPanel.style.display = open ? "flex" : "none";
    if (p.optChevron) p.optChevron.style.transform = open ? "rotate(90deg)" : "rotate(0deg)";
    node.properties = node.properties || {};
    node.properties._erpkOptionsOpen = open;
    if (adjustSize && was !== open) {
        const delta = open ? OPTIONS_PANEL_HEIGHT : -OPTIONS_PANEL_HEIGHT;
        node.size[1] = Math.max(MIN_NODE_HEIGHT, (node.size[1] || MIN_NODE_HEIGHT) + delta);
        clampRootToNodeWidth(node);
        node.setDirtyCanvas?.(true, true);
    }
}

// Pick a sensible column count for the gallery grid based on image count.
// Matches how ComfyUI's native Preview Image lays things out — large thumbs
// for small N, denser grid for larger N.
function computeGalleryCols(n) {
    if (n <= 2) return n;
    if (n <= 4) return 2;
    if (n <= 9) return 3;
    return 4;
}

const SAFE_URL_SCHEMES = /^(https?:|mailto:|\/|\.\/|#)/i;

function sanitizeHref(url) {
    if (typeof url !== "string") return "#";
    const trimmed = url.trim();
    return SAFE_URL_SCHEMES.test(trimmed) ? trimmed : "#";
}

function triggerBrowserDownload(url, filename) {
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
}

async function downloadPayload(payload) {
    const base = (payload.filename || "preview").replace(/[^A-Za-z0-9_\-]+/g, "_");
    const ext = EXT_FOR_KIND[payload.kind] || "";

    if (payload.text !== undefined) {
        const mime = payload.kind === "markdown" ? "text/markdown" : "text/plain";
        const blob = new Blob([payload.text], { type: mime });
        const url = URL.createObjectURL(blob);
        triggerBrowserDownload(url, base + ext);
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        return;
    }

    // Image gallery: download all N images as separate files. Browsers
    // rate-limit back-to-back programmatic downloads once the user-gesture
    // context expires (~1s after the click). To work around, we pre-fetch
    // all blobs in parallel, then trigger the <a download> sequentially
    // with a small delay between each — keeps each click within the
    // browser's "allow multi-download" window.
    if (payload.kind === "image_gallery" && Array.isArray(payload.urls)) {
        if (payload.urls.length > 1) {
            console.log(
                `[ERPK PreviewAnything] downloading ${payload.urls.length} images. ` +
                `Browsers may prompt for permission on multi-file download — click Allow.`
            );
        }
        // Fetch all blobs in parallel first (fast; they're usually /view? from the same origin).
        const fetched = await Promise.all(
            payload.urls.map(async (u, i) => {
                try {
                    const response = await fetch(u);
                    if (!response.ok) throw new Error(`HTTP ${response.status}`);
                    const blob = await response.blob();
                    return { url: u, blob, index: i, ok: true };
                } catch (e) {
                    console.warn("[ERPK PreviewAnything] fetch failed for", u, e);
                    return { url: u, blob: null, index: i, ok: false };
                }
            })
        );
        // Now trigger downloads sequentially with small delays so the browser
        // treats them as one user-gesture batch.
        for (let i = 0; i < fetched.length; i++) {
            const entry = fetched[i];
            if (!entry.ok) {
                window.open(entry.url, "_blank", "noopener,noreferrer");
                continue;
            }
            const objUrl = URL.createObjectURL(entry.blob);
            const derivedExt = guessExtFromUrl(entry.url) || ".png";
            triggerBrowserDownload(objUrl, `${base}_${entry.index + 1}${derivedExt}`);
            setTimeout(() => URL.revokeObjectURL(objUrl), 2000);
            if (i < fetched.length - 1) {
                // 180ms is empirically enough for Chrome/Firefox/Safari to
                // queue the download before the next click arrives.
                await new Promise((r) => setTimeout(r, 180));
            }
        }
        return;
    }

    if (!payload.url) return;

    try {
        const response = await fetch(payload.url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const derivedExt = guessExtFromUrl(payload.url) || ext;
        triggerBrowserDownload(url, base + derivedExt);
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) {
        console.warn("[ERPK PreviewAnything] direct download failed, opening URL in new tab:", e);
        window.open(payload.url, "_blank", "noopener,noreferrer");
    }
}

function guessExtFromUrl(url) {
    try {
        const path = new URL(url, window.location.origin).pathname;
        const idx = path.lastIndexOf(".");
        if (idx === -1) return "";
        const ext = path.slice(idx).toLowerCase();
        return ext.length <= 6 ? ext : "";
    } catch (_) {
        return "";
    }
}

// --- Markdown rendering via DOM APIs (no innerHTML) ---
// Supports: fenced code blocks, headings, unordered lists, blockquotes,
// bold (**text**), italic (*text*), inline code, and [label](url) links.

const INLINE_PATTERN = /(\*\*[^*]+\*\*|\*[^*\n]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;

function appendInlineMarkdown(parent, text) {
    let lastIndex = 0;
    for (const match of text.matchAll(INLINE_PATTERN)) {
        if (match.index > lastIndex) {
            parent.appendChild(document.createTextNode(text.slice(lastIndex, match.index)));
        }
        const token = match[0];
        if (token.startsWith("**")) {
            const strong = document.createElement("strong");
            strong.textContent = token.slice(2, -2);
            parent.appendChild(strong);
        } else if (token.startsWith("`")) {
            const code = document.createElement("code");
            code.textContent = token.slice(1, -1);
            parent.appendChild(code);
        } else if (token.startsWith("[")) {
            const close = token.indexOf("](");
            const label = token.slice(1, close);
            const href = token.slice(close + 2, -1);
            const a = document.createElement("a");
            a.href = sanitizeHref(href);
            a.target = "_blank";
            a.rel = "noopener noreferrer";
            a.textContent = label;
            parent.appendChild(a);
        } else {
            const em = document.createElement("em");
            em.textContent = token.slice(1, -1);
            parent.appendChild(em);
        }
        lastIndex = match.index + token.length;
    }
    if (lastIndex < text.length) {
        parent.appendChild(document.createTextNode(text.slice(lastIndex)));
    }
}

function renderMarkdownInto(container, text) {
    const lines = (text ?? "").split("\n");
    let i = 0;
    let currentList = null;

    const flushList = () => { currentList = null; };

    while (i < lines.length) {
        const line = lines[i];

        // Fenced code block
        if (/^```/.test(line)) {
            flushList();
            const codeLines = [];
            i++;
            while (i < lines.length && !/^```/.test(lines[i])) {
                codeLines.push(lines[i]);
                i++;
            }
            i++; // skip closing fence
            const pre = document.createElement("pre");
            const code = document.createElement("code");
            code.textContent = codeLines.join("\n");
            pre.appendChild(code);
            container.appendChild(pre);
            continue;
        }

        // Heading
        const h = line.match(/^(#{1,6})\s+(.+)$/);
        if (h) {
            flushList();
            const tag = `h${h[1].length}`;
            const el = document.createElement(tag);
            appendInlineMarkdown(el, h[2]);
            container.appendChild(el);
            i++;
            continue;
        }

        // Blockquote
        const bq = line.match(/^>\s+(.+)$/);
        if (bq) {
            flushList();
            const el = document.createElement("blockquote");
            appendInlineMarkdown(el, bq[1]);
            container.appendChild(el);
            i++;
            continue;
        }

        // Unordered list item
        const li = line.match(/^\s*[-*+]\s+(.+)$/);
        if (li) {
            if (!currentList) {
                currentList = document.createElement("ul");
                container.appendChild(currentList);
            }
            const item = document.createElement("li");
            appendInlineMarkdown(item, li[1]);
            currentList.appendChild(item);
            i++;
            continue;
        }

        flushList();

        // Blank line → paragraph separator
        if (line.trim() === "") {
            i++;
            continue;
        }

        // Paragraph: collect consecutive non-empty, non-block lines
        const paraLines = [line];
        i++;
        while (
            i < lines.length
            && lines[i].trim() !== ""
            && !/^(#{1,6}\s|```|>\s|\s*[-*+]\s)/.test(lines[i])
        ) {
            paraLines.push(lines[i]);
            i++;
        }
        const p = document.createElement("p");
        paraLines.forEach((pl, idx) => {
            if (idx > 0) p.appendChild(document.createElement("br"));
            appendInlineMarkdown(p, pl);
        });
        container.appendChild(p);
    }
}

// Pin the DOM widget's root element to the current node width in px.
// ComfyUI positions DOM widgets in an absolutely-placed wrapper whose
// width is set via JavaScript on each canvas draw, not via CSS. On
// workflow load and on initial creation, that wrapper sometimes resolves
// to a stale value before our size floor is applied, leaving root's
// `width: 100%` sized against the wrong containing block. Writing an
// explicit px width here is the belt-and-suspenders fix — applied from
// onNodeCreated, onConfigure, and onResize so every "size has changed"
// path reaches it.
//
// CHROME_HORIZONTAL_INSET accounts for the per-side inset that ComfyUI
// applies between the outer node frame and the inner widget area (the
// same inset that makes canvas-drawn widgets like `display_type` sit
// flush with the rounded card edges in both the legacy and Vue
// renderers). Without subtracting it from node.size[0], the DOM widget
// renders past the inner edge on the right side.
const CHROME_HORIZONTAL_INSET = 16;

function clampRootToNodeWidth(node) {
    const root = node?._erpkPreview?.root;
    if (!root) return;
    const outer = Math.max(node.size?.[0] ?? 320, 100);
    const w = Math.max(outer - CHROME_HORIZONTAL_INSET, 100);
    root.style.width = w + "px";
    root.style.maxWidth = w + "px";
}

// Build the styled Options panel that stands in for the hidden canvas widgets.
// Returns the bar (click target), the chevron, the collapsible panel, and the
// three controls. Wiring to the node's widgets happens in onNodeCreated.
function buildOptions() {
    const optBar = document.createElement("div");
    optBar.className = "erpk-pa-optbar";
    optBar.setAttribute("role", "button");
    optBar.setAttribute("tabindex", "0");
    optBar.setAttribute("aria-label", "Toggle options");

    const gear = document.createElement("span");
    gear.className = "erpk-pa-gear";
    gear.textContent = "⚙";
    const barLabel = document.createElement("span");
    barLabel.textContent = "Options";
    const optChevron = document.createElement("span");
    optChevron.className = "erpk-pa-chevron";
    optChevron.textContent = "▸";
    optBar.appendChild(gear);
    optBar.appendChild(barLabel);
    optBar.appendChild(optChevron);

    const optPanel = document.createElement("div");
    optPanel.className = "erpk-pa-optpanel";
    optPanel.style.display = "none";

    const field = (labelText, control) => {
        const row = document.createElement("div");
        row.className = "erpk-pa-field";
        const lbl = document.createElement("span");
        lbl.className = "erpk-pa-flabel";
        lbl.textContent = labelText;
        row.appendChild(lbl);
        row.appendChild(control);
        return row;
    };

    const selDisplay = document.createElement("select");
    selDisplay.className = "erpk-pa-select";
    for (const opt of DISPLAY_TYPES) {
        const o = document.createElement("option");
        o.value = opt;
        o.textContent = opt;
        selDisplay.appendChild(o);
    }

    const inpFilename = document.createElement("input");
    inpFilename.type = "text";
    inpFilename.className = "erpk-pa-input";
    inpFilename.placeholder = "preview";

    const swStrip = document.createElement("button");
    swStrip.type = "button";
    swStrip.className = "erpk-pa-switch";
    swStrip.setAttribute("role", "switch");
    swStrip.setAttribute("aria-checked", "false");
    swStrip.setAttribute("aria-label", "Strip metadata");
    const knob = document.createElement("span");
    knob.className = "erpk-pa-knob";
    swStrip.appendChild(knob);
    const stripRow = field("Strip metadata", swStrip);
    stripRow.style.justifyContent = "space-between";

    optPanel.appendChild(field("Display as", selDisplay));
    optPanel.appendChild(field("Filename", inpFilename));
    optPanel.appendChild(stripRow);

    return { optBar, optChevron, optPanel, selDisplay, inpFilename, swStrip };
}

function buildContainer() {
    ensureStyles();

    const root = document.createElement("div");
    root.className = "erpk-preview-anything";
    root.style.display = "flex";
    root.style.flexDirection = "column";
    root.style.gap = "6px";
    root.style.padding = "6px";
    root.style.boxSizing = "border-box";
    root.style.width = "100%";
    root.style.height = "100%";
    root.style.minHeight = "120px";
    root.style.overflow = "hidden";

    const { optBar, optChevron, optPanel, selDisplay, inpFilename, swStrip } = buildOptions();

    const content = document.createElement("div");
    content.className = "erpk-preview-anything-content";
    // flex: 1 1 0 lets content fill available space; min-height: 0 allows
    // flex-shrink below its intrinsic size so the toolbar is never pushed out.
    content.style.flex = "1 1 0";
    content.style.minHeight = "0";
    content.style.width = "100%";
    content.style.overflow = "auto";
    content.style.boxSizing = "border-box";
    content.style.background = "var(--erpk-pa-stage, #101014)";
    content.style.border = "1px solid var(--erpk-pa-line, rgba(255,255,255,0.08))";
    content.style.borderRadius = "8px";
    content.style.padding = "8px";
    content.style.color = "var(--erpk-pa-text, #e6e6ea)";
    content.style.fontSize = "12px";
    content.style.fontFamily = "var(--font-family, 'Segoe UI', sans-serif)";

    const empty = document.createElement("div");
    empty.className = "erpk-pa-empty";
    empty.textContent = EMPTY_TEXT;
    content.appendChild(empty);

    const toolbar = document.createElement("div");
    toolbar.style.gap = "6px";
    // flex: 0 0 auto keeps the toolbar at its natural height — it never
    // shrinks, so the Download button stays visible even when content overflows.
    toolbar.style.flex = "0 0 auto";
    toolbar.style.width = "100%";
    // Hidden until a payload arrives — the action buttons only make sense when
    // there is something to copy or download.
    toolbar.style.display = "none";

    const charCount = document.createElement("span");
    charCount.className = "erpk-char-count";
    charCount.style.display = "none";
    charCount.style.flex = "1 1 auto";
    charCount.textContent = "";

    const copyBtn = document.createElement("button");
    copyBtn.type = "button";
    copyBtn.className = "erpk-copy-btn";
    copyBtn.style.flex = "0 0 auto";
    copyBtn.style.padding = "8px 12px";
    copyBtn.style.borderRadius = "8px";
    copyBtn.style.transition = "background 120ms ease";
    copyBtn.style.display = "none";

    const copyLabel = document.createElement("span");
    copyLabel.className = "erpk-copy-label";
    copyLabel.textContent = "Copy";
    copyLabel.style.pointerEvents = "none";
    copyBtn.appendChild(copyLabel);

    const downloadBtn = document.createElement("button");
    downloadBtn.type = "button";
    downloadBtn.className = "erpk-download-btn";
    downloadBtn.style.flex = "1 1 auto";
    downloadBtn.style.minWidth = "120px";
    downloadBtn.style.padding = "8px 12px";
    downloadBtn.style.borderRadius = "8px";
    downloadBtn.style.transition = "background 120ms ease";
    downloadBtn.style.display = "none";

    const label = document.createElement("span");
    label.className = "erpk-download-label";
    label.textContent = "Download";
    label.style.pointerEvents = "none";
    downloadBtn.appendChild(label);

    // All visual state (including hover) is owned by the injected stylesheet,
    // keyed on :disabled / :hover pseudo-classes. No inline JS tweaking needed.
    const syncDisabledStyle = () => { /* handled by CSS via :disabled */ };
    toolbar.appendChild(charCount);
    toolbar.appendChild(copyBtn);
    toolbar.appendChild(downloadBtn);

    root.appendChild(optBar);
    root.appendChild(optPanel);
    root.appendChild(content);
    root.appendChild(toolbar);

    return {
        root, toolbar, content, empty, downloadBtn, copyBtn, copyLabel, charCount,
        optBar, optChevron, optPanel, selDisplay, inpFilename, swStrip, syncDisabledStyle,
    };
}

// Toggle and update toolbar state based on payload kind.
// Text/markdown get a character count and a Copy button.
// Image galleries get an adaptive download label ("Download all (N)" in grid,
// "Download image" when in single-image zoom — the gallery's showGrid/showSingle
// update the label live).
// Everything else hides the text tools and uses a plain "Download" label.
function updateToolbarForKind(preview, payload) {
    const kind = payload?.kind;
    const isText = kind === "text" || kind === "markdown";
    const isImage = kind === "image" || kind === "gif";
    const isGallery = kind === "image_gallery";

    // A payload exists, so reveal the toolbar and its always-relevant Download
    // button. Copy / char-count visibility is decided per-kind below.
    if (preview.toolbar) preview.toolbar.style.display = "flex";
    if (preview.downloadBtn) {
        preview.downloadBtn.style.display = "inline-flex";
        preview.downloadBtn.disabled = false;
    }

    // Char count is only meaningful for text-ish content
    if (isText) {
        const text = payload?.text || "";
        preview.charCount.style.display = "inline-flex";
        preview.charCount.textContent = `${text.length.toLocaleString()} chars`;
    } else {
        preview.charCount.style.display = "none";
    }

    // Copy button: visible for text (copy text), single image/gif (copy image blob),
    // and gallery — but in gallery we defer the visibility to showGrid/showSingle
    // since the semantics change per-mode (hidden in grid, visible in single).
    if (isText) {
        preview.copyBtn.style.display = "inline-flex";
        preview.copyBtn.disabled = (payload?.text || "").length === 0;
    } else if (isImage) {
        preview.copyBtn.style.display = "inline-flex";
        preview.copyBtn.disabled = false;
    } else if (isGallery) {
        // Gallery starts in grid mode — copy button stays hidden until the user
        // opens the single-image zoom. showSingle/showGrid flip it.
        preview.copyBtn.style.display = "none";
    } else {
        preview.copyBtn.style.display = "none";
    }

    const dlLabel = preview.downloadBtn?.querySelector(".erpk-download-label");
    if (dlLabel) {
        if (isGallery) {
            const n = Array.isArray(payload.urls) ? payload.urls.length : 0;
            dlLabel.textContent = `Download all (${n})`;
        } else {
            dlLabel.textContent = "Download";
        }
    }

    // Reset gallery state on any new payload; gallery re-sets these if relevant.
    preview.galleryMode = null;
    preview.galleryCurrentIdx = null;
}

function clearChildren(el) {
    while (el.firstChild) el.removeChild(el.firstChild);
}

// Subtle on-theme stand-in shown when an image URL fails to load (e.g. a stale
// /view temp file from a prior run that has since expired). Reuses the empty-
// state styling so a failed preview reads as "nothing here" rather than the
// browser's broken-image glyph.
function imageFallback(message) {
    const el = document.createElement("div");
    el.className = "erpk-pa-empty";
    el.textContent = message || "Preview unavailable";
    return el;
}

// Reset the node to its clean "ready to queue" state: empty content, no
// toolbar, no payload. Used when a restored media preview can't load — after a
// ComfyUI restart its temp file is gone, so there is nothing to show or
// download and the node should look freshly placed, not stuck on a dead frame.
function showEmptyState(preview) {
    if (!preview) return;
    clearChildren(preview.content);
    const empty = document.createElement("div");
    empty.className = "erpk-pa-empty";
    empty.textContent = EMPTY_TEXT;
    preview.content.appendChild(empty);
    if (preview.toolbar) preview.toolbar.style.display = "none";
    if (preview.copyBtn) preview.copyBtn.style.display = "none";
    if (preview.charCount) preview.charCount.style.display = "none";
    if (preview.downloadBtn) preview.downloadBtn.style.display = "none";
    preview.payload = null;
}

// Build a two-state gallery widget for image_gallery payloads.
// Default: CSS-grid of thumbnails with hover-revealed "W × H" tags.
// Click a thumbnail -> single/zoom view of that image with a close (×)
// button top-right and a "N/M" pagination badge bottom-right. Arrow
// keys navigate, Escape returns to the grid. Keyboard listener is only
// attached while the single view is active to avoid leaks.
function buildImageGallery(urls, filenameBase, preview) {
    const wrapper = document.createElement("div");
    wrapper.className = "erpk-gallery";
    wrapper.style.position = "relative";
    wrapper.style.width = "100%";
    wrapper.style.height = "100%";
    wrapper.style.display = "flex";
    wrapper.style.flexDirection = "column";

    const header = document.createElement("div");
    header.className = "erpk-gallery-header";
    header.style.fontSize = "11px";
    header.style.color = "var(--input-text, #888)";
    header.style.padding = "2px 4px 6px 4px";
    header.style.flex = "0 0 auto";
    header.textContent = `${urls.length} image${urls.length === 1 ? "" : "s"}`;
    wrapper.appendChild(header);

    const cols = computeGalleryCols(urls.length);
    const rows = Math.ceil(urls.length / cols);
    const gridView = document.createElement("div");
    gridView.className = "erpk-gallery-grid";
    gridView.style.display = "grid";
    gridView.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
    // Explicit row tracks let cells divide the grid's allocated height
    // instead of inheriting a width-derived size from `aspect-ratio:1/1`,
    // which would otherwise force the grid to overflow when the content
    // area is shorter than its width × rows.
    gridView.style.gridTemplateRows = `repeat(${rows}, 1fr)`;
    gridView.style.gap = "6px";
    gridView.style.width = "100%";
    gridView.style.flex = "1 1 auto";
    gridView.style.minHeight = "0";

    const singleView = document.createElement("div");
    singleView.className = "erpk-gallery-single";
    singleView.style.display = "none";
    singleView.style.position = "relative";
    singleView.style.width = "100%";
    singleView.style.height = "100%";
    singleView.style.flex = "1 1 auto";

    let currentIdx = 0;
    let keyHandler = null;

    function getDownloadLabel() {
        return preview?.downloadBtn?.querySelector(".erpk-download-label") || null;
    }

    // ---- Grid thumbnails -----------------------------------------
    urls.forEach((url, idx) => {
        const cell = document.createElement("div");
        cell.className = "erpk-gallery-cell";
        cell.style.position = "relative";
        // Cells fill their grid track (sized by gridTemplateRows × gridTemplateColumns
        // at `1fr` each). `min-*: 0` lets the cell shrink below its intrinsic image
        // size so the grid never overflows the content area.
        cell.style.minWidth = "0";
        cell.style.minHeight = "0";
        cell.style.overflow = "hidden";
        cell.style.borderRadius = "4px";
        cell.style.cursor = "pointer";
        cell.style.background = "var(--erpk-pa-stage, #101014)";
        cell.style.border = "1px solid var(--erpk-pa-line, rgba(255,255,255,0.08))";

        const img = document.createElement("img");
        img.src = url;
        img.alt = `${filenameBase || "image"}_${idx + 1}`;
        img.style.width = "100%";
        img.style.height = "100%";
        img.style.objectFit = "cover";
        img.style.display = "block";

        const dims = document.createElement("div");
        dims.className = "erpk-gallery-dims";
        dims.style.position = "absolute";
        dims.style.bottom = "4px";
        dims.style.right = "4px";
        dims.style.padding = "2px 6px";
        dims.style.background = "rgba(0, 0, 0, 0.75)";
        dims.style.color = "#fff";
        dims.style.fontSize = "10px";
        dims.style.fontWeight = "600";
        dims.style.borderRadius = "3px";
        dims.style.opacity = "0";
        dims.style.transition = "opacity 120ms ease";
        dims.style.pointerEvents = "none";

        img.addEventListener("load", () => {
            if (img.naturalWidth && img.naturalHeight) {
                dims.textContent = `${img.naturalWidth} × ${img.naturalHeight}`;
            }
        }, { once: true });

        img.addEventListener("error", () => {
            clearChildren(cell);
            const fallback = imageFallback("n/a");
            fallback.style.fontSize = "11px";
            fallback.style.padding = "4px";
            cell.appendChild(fallback);
        }, { once: true });

        cell.addEventListener("mouseenter", () => { dims.style.opacity = "1"; });
        cell.addEventListener("mouseleave", () => { dims.style.opacity = "0"; });
        cell.addEventListener("click", (e) => {
            e.stopPropagation();
            currentIdx = idx;
            showSingle();
        });

        cell.appendChild(img);
        cell.appendChild(dims);
        gridView.appendChild(cell);
    });

    // ---- Single / zoom view --------------------------------------
    const singleImg = document.createElement("img");
    singleImg.className = "erpk-gallery-single-img";
    singleImg.style.width = "100%";
    singleImg.style.height = "auto";
    singleImg.style.maxHeight = "calc(100% - 30px)";
    singleImg.style.objectFit = "contain";
    singleImg.style.display = "block";
    singleImg.style.background = "var(--erpk-pa-stage, #101014)";
    singleImg.style.borderRadius = "4px";

    const singleCaption = document.createElement("div");
    singleCaption.className = "erpk-gallery-caption";
    singleCaption.style.textAlign = "center";
    singleCaption.style.fontSize = "11px";
    singleCaption.style.color = "var(--input-text, #888)";
    singleCaption.style.padding = "6px 0";
    singleCaption.style.fontVariantNumeric = "tabular-nums";

    const closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.className = "erpk-gallery-close";
    closeBtn.textContent = "×";
    closeBtn.setAttribute("aria-label", "Close expanded view");
    closeBtn.style.position = "absolute";
    closeBtn.style.top = "6px";
    closeBtn.style.right = "6px";
    closeBtn.style.width = "28px";
    closeBtn.style.height = "28px";
    closeBtn.style.padding = "0";
    closeBtn.style.background = "rgba(0, 0, 0, 0.8)";
    closeBtn.style.color = "#fff";
    closeBtn.style.border = "1px solid #555";
    closeBtn.style.borderRadius = "4px";
    closeBtn.style.cursor = "pointer";
    closeBtn.style.fontSize = "18px";
    closeBtn.style.lineHeight = "1";
    closeBtn.style.zIndex = "4";
    closeBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        showGrid();
    });

    // Previous / Next navigation buttons for single view
    const prevBtn = document.createElement("button");
    prevBtn.type = "button";
    prevBtn.className = "erpk-gallery-nav-btn erpk-gallery-prev";
    prevBtn.textContent = "‹";
    prevBtn.setAttribute("aria-label", "Previous image");
    prevBtn.style.left = "6px";
    prevBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        if (currentIdx > 0) {
            currentIdx -= 1;
            updateSingle();
        }
    });

    const nextBtn = document.createElement("button");
    nextBtn.type = "button";
    nextBtn.className = "erpk-gallery-nav-btn erpk-gallery-next";
    nextBtn.textContent = "›";
    nextBtn.setAttribute("aria-label", "Next image");
    nextBtn.style.right = "6px";
    nextBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        if (currentIdx < urls.length - 1) {
            currentIdx += 1;
            updateSingle();
        }
    });

    const pagination = document.createElement("div");
    pagination.className = "erpk-gallery-pagination";
    pagination.style.position = "absolute";
    pagination.style.bottom = "34px";
    pagination.style.right = "6px";
    pagination.style.padding = "4px 10px";
    pagination.style.background = "rgba(0, 0, 0, 0.8)";
    pagination.style.color = "#fff";
    pagination.style.fontSize = "12px";
    pagination.style.fontWeight = "600";
    pagination.style.borderRadius = "4px";
    pagination.style.pointerEvents = "none";
    pagination.style.fontVariantNumeric = "tabular-nums";

    singleView.appendChild(singleImg);
    singleView.appendChild(singleCaption);
    singleView.appendChild(closeBtn);
    singleView.appendChild(pagination);
    singleView.appendChild(prevBtn);
    singleView.appendChild(nextBtn);

    function updateSingle() {
        singleImg.style.display = "block";  // reset in case a prior image failed
        singleImg.src = urls[currentIdx];
        pagination.textContent = `${currentIdx + 1}/${urls.length}`;
        singleCaption.textContent = "";  // cleared until load
        singleImg.addEventListener("load", () => {
            if (singleImg.naturalWidth && singleImg.naturalHeight) {
                singleCaption.textContent = `${singleImg.naturalWidth} × ${singleImg.naturalHeight}`;
            }
        }, { once: true });
        singleImg.addEventListener("error", () => {
            singleImg.style.display = "none";
            singleCaption.textContent = "Preview unavailable";
        }, { once: true });
        prevBtn.disabled = currentIdx === 0;
        nextBtn.disabled = currentIdx === urls.length - 1;
        if (preview) {
            preview.galleryMode = "single";
            preview.galleryCurrentIdx = currentIdx;
        }
    }

    function onKey(e) {
        if (e.key === "Escape") {
            e.preventDefault();
            showGrid();
        } else if (e.key === "ArrowLeft") {
            if (currentIdx > 0) {
                e.preventDefault();
                currentIdx -= 1;
                updateSingle();
            }
        } else if (e.key === "ArrowRight") {
            if (currentIdx < urls.length - 1) {
                e.preventDefault();
                currentIdx += 1;
                updateSingle();
            }
        }
    }

    function showSingle() {
        header.style.display = "none";
        gridView.style.display = "none";
        singleView.style.display = "block";
        updateSingle();
        const dlLabel = getDownloadLabel();
        if (dlLabel) dlLabel.textContent = "Download image";
        // In single/zoom mode, copy button is meaningful (copies this image).
        if (preview?.copyBtn) {
            preview.copyBtn.style.display = "inline-flex";
            preview.copyBtn.disabled = false;
        }
        if (!keyHandler) {
            keyHandler = onKey;
            document.addEventListener("keydown", keyHandler);
        }
    }

    function showGrid() {
        header.style.display = "";
        gridView.style.display = "grid";
        singleView.style.display = "none";
        if (preview) {
            preview.galleryMode = "grid";
            preview.galleryCurrentIdx = null;
        }
        const dlLabel = getDownloadLabel();
        if (dlLabel) dlLabel.textContent = `Download all (${urls.length})`;
        // Grid mode has no single target to copy; hide the copy button.
        if (preview?.copyBtn) {
            preview.copyBtn.style.display = "none";
        }
        if (keyHandler) {
            document.removeEventListener("keydown", keyHandler);
            keyHandler = null;
        }
    }

    // Initialize preview state for this gallery (grid is the default view)
    if (preview) {
        preview.galleryMode = "grid";
        preview.galleryCurrentIdx = null;
    }

    wrapper.appendChild(gridView);
    wrapper.appendChild(singleView);
    return wrapper;
}

// opts.onMediaError, when supplied, is invoked instead of the inline "Preview
// unavailable" fallback if a media resource (image / gif / video / audio) fails
// to load. The restore path uses it to degrade a dead temp-file preview to the
// clean empty state.
function renderInto(content, payload, preview, opts = {}) {
    clearChildren(content);

    if (!payload) {
        content.textContent = "No content.";
        return;
    }

    const kind = payload.kind || "text";

    if (kind === "image" || kind === "gif") {
        // Flex-centered wrapper so the image sits in the middle of whatever
        // shape the node currently has. The image hugs its own rendered
        // size via max-* + auto, so the dims overlay anchors to the image
        // (not the wrapper) — no floating-in-letterbox-space surprise.
        const wrapper = document.createElement("div");
        wrapper.style.position = "relative";
        wrapper.style.width = "100%";
        wrapper.style.height = "100%";
        wrapper.style.display = "flex";
        wrapper.style.alignItems = "center";
        wrapper.style.justifyContent = "center";

        const img = document.createElement("img");
        img.src = payload.url;
        img.alt = payload.filename || "image";
        img.style.maxWidth = "100%";
        img.style.maxHeight = "100%";
        img.style.width = "auto";
        img.style.height = "auto";
        img.style.display = "block";
        img.style.borderRadius = "3px";

        // Dimension badge — small overlay in the bottom-right, same language
        // the gallery uses so the whole node speaks consistently.
        const dims = document.createElement("div");
        dims.className = "erpk-image-dims";
        dims.style.position = "absolute";
        dims.style.bottom = "6px";
        dims.style.right = "6px";
        dims.style.padding = "3px 8px";
        dims.style.background = "rgba(0, 0, 0, 0.75)";
        dims.style.color = "#fff";
        dims.style.fontSize = "11px";
        dims.style.fontWeight = "600";
        dims.style.borderRadius = "3px";
        dims.style.pointerEvents = "none";
        dims.style.fontVariantNumeric = "tabular-nums";
        dims.style.opacity = "0";
        dims.style.transition = "opacity 120ms ease";
        dims.textContent = "";

        img.addEventListener("load", () => {
            if (img.naturalWidth && img.naturalHeight) {
                dims.textContent = `${img.naturalWidth} × ${img.naturalHeight}`;
                dims.style.opacity = "1";
            }
        }, { once: true });

        img.addEventListener("error", () => {
            if (opts.onMediaError) { opts.onMediaError(); return; }
            clearChildren(wrapper);
            wrapper.appendChild(imageFallback("Preview unavailable"));
        }, { once: true });

        wrapper.appendChild(img);
        wrapper.appendChild(dims);
        content.appendChild(wrapper);
        return;
    }

    if (kind === "image_gallery") {
        const urls = Array.isArray(payload.urls) ? payload.urls : [];
        // Pass preview so the gallery can drive the download button's label
        // and track grid/single view state.
        const gallery = buildImageGallery(urls, payload.filename, preview);
        content.appendChild(gallery);
        return;
    }

    if (kind === "video") {
        // Centering + max-width/height keeps the video proportional and
        // as large as possible within whatever shape content takes.
        const wrapper = document.createElement("div");
        wrapper.style.width = "100%";
        wrapper.style.height = "100%";
        wrapper.style.display = "flex";
        wrapper.style.alignItems = "center";
        wrapper.style.justifyContent = "center";

        const video = document.createElement("video");
        video.src = payload.url;
        video.controls = true;
        video.preload = "metadata";
        video.style.maxWidth = "100%";
        video.style.maxHeight = "100%";
        video.style.display = "block";
        video.style.borderRadius = "3px";
        video.addEventListener("error", () => {
            if (opts.onMediaError) { opts.onMediaError(); return; }
            clearChildren(wrapper);
            wrapper.appendChild(imageFallback("Preview unavailable"));
        }, { once: true });
        wrapper.appendChild(video);
        content.appendChild(wrapper);
        return;
    }

    if (kind === "audio") {
        const audio = document.createElement("audio");
        audio.src = payload.url;
        audio.controls = true;
        audio.preload = "metadata";
        audio.style.width = "100%";
        audio.style.display = "block";
        audio.addEventListener("error", () => {
            if (opts.onMediaError) { opts.onMediaError(); return; }
            clearChildren(content);
            content.appendChild(imageFallback("Preview unavailable"));
        }, { once: true });
        content.appendChild(audio);
        return;
    }

    if (kind === "markdown") {
        const md = document.createElement("div");
        md.className = "erpk-preview-markdown";
        md.style.lineHeight = "1.5";
        renderMarkdownInto(md, payload.text || "");
        content.appendChild(md);
        return;
    }

    const pre = document.createElement("pre");
    pre.style.margin = "0";
    pre.style.whiteSpace = "pre-wrap";
    pre.style.wordBreak = "break-word";
    pre.style.fontFamily = "var(--font-family-monospace, ui-monospace, Menlo, monospace)";
    pre.textContent = payload.text || "";
    content.appendChild(pre);
}

app.registerExtension({
    name: "erpk.utils.preview_anything",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE_ID) return;

        // Enforce a hard minimum size at the LiteGraph layer. The canvas
        // renderer reads `computeSize` when drag-resizing and clamps the
        // dragged dimensions to at least that. Without this override, the
        // node would let the user drag below the height needed for the
        // toolbar and content area, pushing them outside the node body.
        const origComputeSize = nodeType.prototype.computeSize;
        nodeType.prototype.computeSize = function () {
            const size = origComputeSize?.apply(this, arguments) ?? [320, 260];
            return [Math.max(size[0], 320), Math.max(size[1], 260)];
        };

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = onNodeCreated?.apply(this, arguments);

            const built = buildContainer();
            const {
                root, content, downloadBtn, copyBtn, copyLabel, charCount,
                optBar, selDisplay, inpFilename, swStrip,
            } = built;
            this._erpkPreview = { ...built, payload: null, optionsOpen: false };

            downloadBtn.addEventListener("click", () => {
                const p = this._erpkPreview;
                if (!p.payload) return;
                // Gallery single-view: download only the focused image.
                if (
                    p.payload.kind === "image_gallery"
                    && p.galleryMode === "single"
                    && p.galleryCurrentIdx != null
                    && Array.isArray(p.payload.urls)
                ) {
                    const idx = p.galleryCurrentIdx;
                    downloadPayload({
                        kind: "image",
                        url: p.payload.urls[idx],
                        filename: `${p.payload.filename || "preview"}_${idx + 1}`,
                    });
                    return;
                }
                // All other kinds (including gallery grid mode) use default behavior.
                downloadPayload(p.payload);
            });

            copyBtn.addEventListener("click", async () => {
                const p = this._erpkPreview;
                if (!p.payload) return;
                const kind = p.payload.kind;

                const flashLabel = (text) => {
                    const original = copyLabel.textContent;
                    copyLabel.textContent = text;
                    setTimeout(() => { copyLabel.textContent = original; }, 1500);
                };

                // Text / markdown → copy the text content
                if (kind === "text" || kind === "markdown") {
                    const text = p.payload?.text;
                    if (!text) return;
                    try {
                        await navigator.clipboard.writeText(text);
                        flashLabel("Copied!");
                    } catch (e) {
                        console.error("[ERPK PreviewAnything] Text clipboard copy failed:", e);
                    }
                    return;
                }

                // Determine which image URL to copy based on kind + gallery state
                let imageUrl = null;
                if (kind === "image" || kind === "gif") {
                    imageUrl = p.payload.url;
                } else if (
                    kind === "image_gallery"
                    && p.galleryMode === "single"
                    && p.galleryCurrentIdx != null
                ) {
                    imageUrl = p.payload.urls?.[p.galleryCurrentIdx];
                }
                if (!imageUrl) return;

                // Write the image as a PNG ClipboardItem. Passing a Promise for the
                // blob preserves Safari's user-gesture context (the clipboard.write
                // call happens synchronously inside the click handler).
                try {
                    const item = new ClipboardItem({
                        "image/png": fetch(imageUrl).then((r) => {
                            if (!r.ok) throw new Error(`HTTP ${r.status}`);
                            return r.blob();
                        }),
                    });
                    await navigator.clipboard.write([item]);
                    flashLabel("Copied!");
                } catch (e) {
                    console.warn(
                        "[ERPK PreviewAnything] Image clipboard copy failed, falling back to URL:",
                        e,
                    );
                    try {
                        await navigator.clipboard.writeText(imageUrl);
                        flashLabel("Copied URL");
                    } catch (e2) {
                        console.error(
                            "[ERPK PreviewAnything] URL fallback also failed:",
                            e2,
                        );
                    }
                }
            });

            // Option controls write straight to the hidden canvas widgets, which
            // stay the values serialized and read at queue time. Widgets are
            // looked up lazily so this holds even if they attach slightly after
            // onNodeCreated.
            selDisplay.addEventListener("change", () => {
                const w = findWidget(this, "display_type");
                if (w) { w.value = selDisplay.value; w.callback?.(w.value); }
            });
            inpFilename.addEventListener("input", () => {
                const w = findWidget(this, "filename");
                if (w) { w.value = inpFilename.value; w.callback?.(w.value); }
            });
            swStrip.addEventListener("click", () => {
                const next = swStrip.getAttribute("aria-checked") !== "true";
                swStrip.setAttribute("aria-checked", String(next));
                const w = findWidget(this, "strip_metadata");
                if (w) { w.value = next; w.callback?.(w.value); }
            });

            const toggleOptions = () => setOptionsOpen(this, !this._erpkPreview.optionsOpen, true);
            optBar.addEventListener("click", toggleOptions);
            optBar.addEventListener("keydown", (e) => {
                if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggleOptions(); }
            });

            this.addDOMWidget("preview", "erpk_preview_anything", root, {
                serialize: false,
                hideOnZoom: false,
            });

            // Hide the three config pills; the styled Options panel edits them.
            // V3 can attach a widget a tick late, so retry until all are hidden.
            const ensureHidden = (tries) => {
                if (!this._erpkPreview) return;
                const done = hideConfigWidgets(this);
                syncOptionControls(this);
                clampRootToNodeWidth(this);
                this.setDirtyCanvas?.(true, true);
                if (!done && tries > 0) setTimeout(() => ensureHidden(tries - 1), 50);
            };
            setOptionsOpen(this, false, false);
            ensureHidden(12);

            // 260 high is the floor. User can drag the node taller when they
            // need more room for a gallery or large media.
            if (this.size[1] < 260) this.size[1] = 260;
            if (this.size[0] < 320) this.size[0] = 320;

            clampRootToNodeWidth(this);

            return r;
        };

        const origOnResize = nodeType.prototype.onResize;
        nodeType.prototype.onResize = function (size) {
            const r = origOnResize?.apply(this, arguments);
            clampRootToNodeWidth(this);
            return r;
        };

        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            onExecuted?.apply(this, arguments);

            const payloads = message?.preview_anything;
            if (!Array.isArray(payloads) || payloads.length === 0) return;
            const payload = payloads[0];

            if (!this._erpkPreview) return;
            this._erpkPreview.payload = payload;
            this._erpkPreview.syncDisabledStyle();
            updateToolbarForKind(this._erpkPreview, payload);
            renderInto(this._erpkPreview.content, payload, this._erpkPreview);

            this.properties = this.properties || {};
            this.properties._erpkLastPayload = payload;
        };

        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            const r = onConfigure?.apply(this, arguments);
            // Re-enforce the minimum size: the parent's configure restored
            // info.size from the workflow JSON, which would otherwise lock
            // the node to a stale smaller size from before the floor was raised.
            if (this.size[1] < 260) this.size[1] = 260;
            if (this.size[0] < 320) this.size[0] = 320;
            clampRootToNodeWidth(this);

            // Re-hide the config pills (the parent's configure restored their
            // values) and restore the styled controls + the Options open state.
            // Size is left alone here — the saved node.size already reflects
            // whatever the user had open, so this is a no-resize restore.
            const ensureHiddenOnLoad = (tries) => {
                if (!this._erpkPreview) return;
                const done = hideConfigWidgets(this);
                syncOptionControls(this);
                clampRootToNodeWidth(this);
                this.setDirtyCanvas?.(true, true);
                if (!done && tries > 0) setTimeout(() => ensureHiddenOnLoad(tries - 1), 50);
            };
            if (this._erpkPreview) {
                const savedOpen = info?.properties?._erpkOptionsOpen
                    ?? this.properties?._erpkOptionsOpen ?? false;
                setOptionsOpen(this, !!savedOpen, false);
                ensureHiddenOnLoad(12);
            }

            const saved = info?.properties?._erpkLastPayload
                ?? this.properties?._erpkLastPayload;
            if (saved) {
                setTimeout(() => {
                    if (!this._erpkPreview) return;
                    this._erpkPreview.payload = saved;
                    this._erpkPreview.syncDisabledStyle();
                    updateToolbarForKind(this._erpkPreview, saved);
                    // On a restored preview whose media file is gone (temp wiped
                    // by a ComfyUI restart), fall back to the clean empty state
                    // instead of a stuck "Preview unavailable" + toolbar.
                    renderInto(this._erpkPreview.content, saved, this._erpkPreview, {
                        onMediaError: () => showEmptyState(this._erpkPreview),
                    });
                    syncOptionControls(this);
                    clampRootToNodeWidth(this);
                }, 50);
            }
            return r;
        };
    },
});
