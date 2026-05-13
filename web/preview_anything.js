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
    `;
    document.head.appendChild(style);
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

function buildContainer() {
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

    const content = document.createElement("div");
    content.className = "erpk-preview-anything-content";
    // flex: 1 1 0 lets content fill available space; min-height: 0 allows
    // flex-shrink below its intrinsic size so the toolbar is never pushed out.
    content.style.flex = "1 1 0";
    content.style.minHeight = "0";
    content.style.width = "100%";
    content.style.overflow = "auto";
    content.style.boxSizing = "border-box";
    content.style.background = "var(--comfy-input-bg, #1a1a1a)";
    content.style.border = "1px solid var(--border-color, #333)";
    content.style.borderRadius = "4px";
    content.style.padding = "6px";
    content.style.color = "var(--input-text, #ddd)";
    content.style.fontSize = "12px";
    content.style.fontFamily = "var(--font-family, 'Segoe UI', sans-serif)";
    content.textContent = "No content yet — queue the workflow to preview.";

    const toolbar = document.createElement("div");
    toolbar.style.display = "flex";
    toolbar.style.gap = "6px";
    // flex: 0 0 auto keeps the toolbar at its natural height — it never
    // shrinks, so the Download button stays visible even when content overflows.
    toolbar.style.flex = "0 0 auto";
    toolbar.style.width = "100%";

    ensureStyles();

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
    copyBtn.style.borderRadius = "4px";
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
    downloadBtn.style.borderRadius = "4px";
    downloadBtn.style.transition = "background 120ms ease";
    downloadBtn.disabled = true;

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

    root.appendChild(content);
    root.appendChild(toolbar);

    return { root, toolbar, content, downloadBtn, copyBtn, copyLabel, charCount, syncDisabledStyle };
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
    const gridView = document.createElement("div");
    gridView.className = "erpk-gallery-grid";
    gridView.style.display = "grid";
    gridView.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
    gridView.style.gap = "6px";
    gridView.style.width = "100%";
    gridView.style.flex = "1 1 auto";
    gridView.style.alignContent = "start";

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
        cell.style.aspectRatio = "1 / 1";
        cell.style.overflow = "hidden";
        cell.style.borderRadius = "4px";
        cell.style.cursor = "pointer";
        cell.style.background = "#0a0a0a";
        cell.style.border = "1px solid var(--border-color, #333)";

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
    singleImg.style.background = "#0a0a0a";
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
        singleImg.src = urls[currentIdx];
        pagination.textContent = `${currentIdx + 1}/${urls.length}`;
        singleCaption.textContent = "";  // cleared until load
        singleImg.addEventListener("load", () => {
            if (singleImg.naturalWidth && singleImg.naturalHeight) {
                singleCaption.textContent = `${singleImg.naturalWidth} × ${singleImg.naturalHeight}`;
            }
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

// Grow the node height so the widget's content fits fully inside its
// current rendered rect. Rather than guessing the full node-chrome
// (header + other widgets + padding), we compute the delta between the
// content's natural height and its current rendered height, and add
// that delta to the node's size. Width is left to the user.
function resizeNodeToContent(node) {
    if (!node || typeof node.setSize !== "function") return;

    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            const preview = node._erpkPreview;
            if (!preview?.root) return;

            const contentEl = preview.content;
            const toolbarEl = preview.root.querySelector("button")?.parentElement;

            // Natural height needed: content's intrinsic height + toolbar height +
            // flex gap (6px) + root padding (6*2 = 12px).
            const contentNaturalH = contentEl.scrollHeight;
            const toolbarH = toolbarEl ? toolbarEl.getBoundingClientRect().height : 0;
            const gap = 6;
            const rootPadding = 12;
            const naturalRootH = contentNaturalH + toolbarH + gap + rootPadding;

            const currentRootH = preview.root.getBoundingClientRect().height;
            const delta = naturalRootH - currentRootH;

            if (delta > 2) {
                const newH = (node.size?.[1] || 260) + delta;
                node.setSize([node.size?.[0] || 320, newH]);
                node.setDirtyCanvas?.(true, true);
            }
        });
    });
}

function renderInto(content, payload, onMediaReady, preview) {
    clearChildren(content);
    content.style.aspectRatio = "";
    content.style.height = "";

    if (!payload) {
        content.textContent = "No content.";
        return;
    }

    const kind = payload.kind || "text";
    const notifyReady = () => { if (typeof onMediaReady === "function") onMediaReady(); };

    if (kind === "image" || kind === "gif") {
        const wrapper = document.createElement("div");
        wrapper.style.position = "relative";
        wrapper.style.width = "100%";

        const img = document.createElement("img");
        img.src = payload.url;
        img.alt = payload.filename || "image";
        img.style.width = "100%";
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
                content.style.aspectRatio = `${img.naturalWidth} / ${img.naturalHeight}`;
                dims.textContent = `${img.naturalWidth} × ${img.naturalHeight}`;
                dims.style.opacity = "1";
            }
            notifyReady();
        }, { once: true });

        wrapper.appendChild(img);
        wrapper.appendChild(dims);
        content.appendChild(wrapper);
        return;
    }

    if (kind === "image_gallery") {
        const urls = Array.isArray(payload.urls) ? payload.urls : [];
        // Pass preview so the gallery can drive the download button's label
        // and track grid/single view state. DON'T trigger notifyReady —
        // galleries don't auto-resize the node (would balloon it with empty
        // space on compact grids; user controls node size manually).
        const gallery = buildImageGallery(urls, payload.filename, preview);
        content.appendChild(gallery);
        return;
    }

    if (kind === "video") {
        // Wrapper uses position:absolute to fill content reliably across
        // ComfyUI redraws (right-click context menus trigger layout passes
        // that can confuse percentage heights through flex containers).
        // Centering + max-width/height keeps the video proportional and
        // as large as possible within whatever shape content takes.
        content.style.position = "relative";
        const wrapper = document.createElement("div");
        wrapper.style.position = "absolute";
        wrapper.style.inset = "0";
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
        video.addEventListener("loadedmetadata", () => {
            if (video.videoWidth && video.videoHeight) {
                // Aspect ratio is set so resizeNodeToContent can compute the right
                // initial node height (it runs in 2 rAFs after notifyReady), then
                // we release the constraint so the user can freely resize.
                content.style.aspectRatio = `${video.videoWidth} / ${video.videoHeight}`;
                notifyReady();
                requestAnimationFrame(() => requestAnimationFrame(() => requestAnimationFrame(() => {
                    content.style.aspectRatio = "";
                })));
            } else {
                notifyReady();
            }
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
        audio.addEventListener("loadedmetadata", notifyReady, { once: true });
        content.appendChild(audio);
        return;
    }

    if (kind === "markdown") {
        const md = document.createElement("div");
        md.className = "erpk-preview-markdown";
        md.style.lineHeight = "1.5";
        renderMarkdownInto(md, payload.text || "");
        content.appendChild(md);
        // Text/markdown does NOT resize the node — the content area already
        // scrolls, and long text would otherwise make the node swallow the canvas.
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

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = onNodeCreated?.apply(this, arguments);

            const { root, content, downloadBtn, copyBtn, copyLabel, charCount, syncDisabledStyle } = buildContainer();
            this._erpkPreview = { root, content, downloadBtn, copyBtn, copyLabel, charCount, syncDisabledStyle, payload: null };

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

            this.addDOMWidget("preview", "erpk_preview_anything", root, {
                serialize: false,
                hideOnZoom: false,
            });

            if (this.size[1] < 260) this.size[1] = 260;
            if (this.size[0] < 320) this.size[0] = 320;

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
            this._erpkPreview.downloadBtn.disabled = false;
            this._erpkPreview.syncDisabledStyle();
            updateToolbarForKind(this._erpkPreview, payload);
            renderInto(this._erpkPreview.content, payload, () => resizeNodeToContent(this), this._erpkPreview);

            this.properties = this.properties || {};
            this.properties._erpkLastPayload = payload;
        };

        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            const r = onConfigure?.apply(this, arguments);
            const saved = info?.properties?._erpkLastPayload
                ?? this.properties?._erpkLastPayload;
            if (saved) {
                setTimeout(() => {
                    if (!this._erpkPreview) return;
                    this._erpkPreview.payload = saved;
                    this._erpkPreview.downloadBtn.disabled = false;
                    this._erpkPreview.syncDisabledStyle();
                    updateToolbarForKind(this._erpkPreview, saved);
                    renderInto(this._erpkPreview.content, saved, () => resizeNodeToContent(this), this._erpkPreview);
                }, 50);
            }
            return r;
        };
    },
});
