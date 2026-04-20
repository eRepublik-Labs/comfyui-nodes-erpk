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
    `;
    document.head.appendChild(style);
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
    root.style.minHeight = "80px";
    root.style.overflow = "hidden";

    const content = document.createElement("div");
    content.className = "erpk-preview-anything-content";
    content.style.flex = "0 0 auto";  // shrink to content; let aspect-ratio drive height
    content.style.width = "100%";
    content.style.minHeight = "60px";
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
    toolbar.style.flexShrink = "0";
    toolbar.style.width = "100%";

    ensureStyles();

    const downloadBtn = document.createElement("button");
    downloadBtn.type = "button";
    downloadBtn.className = "erpk-download-btn";
    downloadBtn.style.width = "100%";
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
    toolbar.appendChild(downloadBtn);

    root.appendChild(content);
    root.appendChild(toolbar);

    return { root, toolbar, content, downloadBtn, syncDisabledStyle };
}

function clearChildren(el) {
    while (el.firstChild) el.removeChild(el.firstChild);
}

// Grow the node height to match the current content's natural size.
// LiteGraph keeps node widths under user control, so we only adjust height.
// We never shrink below the user's current size.
function resizeNodeToContent(node) {
    if (!node || typeof node.setSize !== "function") return;
    const minW = Math.max(node.size?.[0] || 320, 320);
    const minH = node.size?.[1] || 260;

    // Let the DOM settle first so scrollHeight reflects the new content.
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            const root = node._erpkPreview?.root;
            if (!root) return;
            const target = root.scrollHeight + 24; // padding + node chrome
            const newH = Math.max(minH, target);
            if (Math.abs(newH - minH) > 2) {
                node.setSize([minW, newH]);
                node.setDirtyCanvas?.(true, true);
            }
        });
    });
}

function renderInto(content, payload, onMediaReady) {
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
        const img = document.createElement("img");
        img.src = payload.url;
        img.alt = payload.filename || "image";
        img.style.width = "100%";
        img.style.height = "auto";
        img.style.display = "block";
        img.style.borderRadius = "3px";
        img.addEventListener("load", () => {
            if (img.naturalWidth && img.naturalHeight) {
                content.style.aspectRatio = `${img.naturalWidth} / ${img.naturalHeight}`;
            }
            notifyReady();
        }, { once: true });
        content.appendChild(img);
        return;
    }

    if (kind === "video") {
        const video = document.createElement("video");
        video.src = payload.url;
        video.controls = true;
        video.preload = "metadata";
        video.style.width = "100%";
        video.style.height = "auto";
        video.style.display = "block";
        video.style.borderRadius = "3px";
        video.addEventListener("loadedmetadata", () => {
            if (video.videoWidth && video.videoHeight) {
                content.style.aspectRatio = `${video.videoWidth} / ${video.videoHeight}`;
            }
            notifyReady();
        }, { once: true });
        content.appendChild(video);
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
        notifyReady();
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

            const { root, content, downloadBtn, syncDisabledStyle } = buildContainer();
            this._erpkPreview = { root, content, downloadBtn, syncDisabledStyle, payload: null };

            downloadBtn.addEventListener("click", () => {
                if (this._erpkPreview.payload) {
                    downloadPayload(this._erpkPreview.payload);
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
            renderInto(this._erpkPreview.content, payload, () => resizeNodeToContent(this));

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
                    renderInto(this._erpkPreview.content, saved, () => resizeNodeToContent(this));
                }, 50);
            }
            return r;
        };
    },
});
