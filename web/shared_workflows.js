// ABOUTME: Registers the ERPK canvas context menu with settings and shared workflow actions
// ABOUTME: Provides modal dialogs for multi-user workflow sharing via /erpk/shared_workflows API

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// ── API helpers ──────────────────────────────────────────────────

async function listSharedWorkflows() {
    const resp = await api.fetchApi("/erpk/shared_workflows");
    if (!resp.ok) return [];
    return await resp.json();
}

async function getSharedWorkflow(name) {
    const resp = await api.fetchApi(
        `/erpk/shared_workflows/${encodeURIComponent(name)}`
    );
    if (!resp.ok) return null;
    return await resp.json();
}

async function saveSharedWorkflow(name, workflow) {
    const resp = await api.fetchApi("/erpk/shared_workflows", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, workflow }),
    });
    return resp;
}

async function deleteSharedWorkflow(name) {
    const resp = await api.fetchApi(
        `/erpk/shared_workflows/${encodeURIComponent(name)}`,
        { method: "DELETE" }
    );
    return resp.ok;
}

// ── Linked workflow state ─────────────────────────────────────────

// Tracks the name of the shared workflow currently loaded on the canvas.
// Set on Load (browse dialog) or Share (save dialog). Enables "Save to [name]".
let linkedSharedWorkflowName = null;

// ── Design system ────────────────────────────────────────────────

const FONT_STACK = "-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif";

const OVERLAY_STYLE =
    "position:fixed;top:0;left:0;width:100%;height:100%;z-index:10000;" +
    "background:rgba(0,0,0,0.7);backdrop-filter:blur(4px);" +
    "display:flex;align-items:center;justify-content:center;" +
    "animation:erpkFadeIn 0.15s ease;";

const DIALOG_STYLE =
    `background:#1c1e28;color:#c8cad0;border:1px solid rgba(255,255,255,0.06);` +
    `border-top:2px solid #4f8ff7;border-radius:12px;` +
    `padding:28px;min-width:440px;max-width:640px;max-height:80vh;` +
    `display:flex;flex-direction:column;font-family:${FONT_STACK};` +
    `box-shadow:0 24px 80px rgba(0,0,0,0.5),0 0 0 1px rgba(255,255,255,0.04);` +
    `animation:erpkSlideUp 0.2s ease;`;

const BUTTON_STYLE =
    "padding:7px 16px;border:1px solid rgba(255,255,255,0.08);border-radius:6px;" +
    "background:rgba(255,255,255,0.04);color:#9ca0b0;cursor:pointer;" +
    "font-size:12px;font-weight:500;letter-spacing:0.02em;" +
    "transition:all 0.15s ease;";

const PRIMARY_BUTTON_STYLE =
    "padding:7px 16px;border:none;border-radius:6px;" +
    "background:linear-gradient(135deg,#4f8ff7,#3d7be5);color:#fff;cursor:pointer;" +
    "font-size:12px;font-weight:600;letter-spacing:0.02em;" +
    "box-shadow:0 2px 8px rgba(79,143,247,0.25);" +
    "transition:all 0.15s ease;";

const DANGER_BUTTON_STYLE =
    "padding:7px 16px;border:1px solid rgba(232,84,84,0.2);border-radius:6px;" +
    "background:rgba(232,84,84,0.08);color:#f07070;cursor:pointer;" +
    "font-size:12px;font-weight:500;letter-spacing:0.02em;" +
    "transition:all 0.15s ease;";

function injectStylesheet() {
    if (document.getElementById("erpk-styles")) return;
    const style = document.createElement("style");
    style.id = "erpk-styles";
    style.textContent = [
        "@keyframes erpkFadeIn{from{opacity:0}to{opacity:1}}",
        "@keyframes erpkSlideUp{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}",
        ".erpk-row:hover{background:rgba(255,255,255,0.03)!important}",
        ".erpk-btn:hover{filter:brightness(1.2);transform:translateY(-1px)}",
        ".erpk-btn:active{transform:translateY(0);filter:brightness(0.95)}",
        ".erpk-input:focus{outline:none;border-color:#4f8ff7!important;box-shadow:0 0 0 2px rgba(79,143,247,0.15)!important}",
    ].join("\n");
    document.head.appendChild(style);
}

// ── Utility ──────────────────────────────────────────────────────

function getActiveWorkflowName() {
    const activeTab = document.querySelector(
        ".p-togglebutton-checked .workflow-label"
    );
    return activeTab?.textContent?.trim() || null;
}

function formatBytes(bytes) {
    if (bytes < 1024) return bytes + " B";
    return (bytes / 1024).toFixed(1) + " KB";
}

function formatDate(mtime) {
    return new Date(mtime * 1000).toLocaleString();
}

function clearChildren(el) {
    while (el.firstChild) el.removeChild(el.firstChild);
}

function showToast(message, severity = "success") {
    const colors = {
        success: { accent: "#43b581", bg: "rgba(67,181,129,0.1)", text: "#7dcea0" },
        error: { accent: "#e85454", bg: "rgba(232,84,84,0.1)", text: "#f07070" },
        info: { accent: "#4f8ff7", bg: "rgba(79,143,247,0.1)", text: "#8bb4f7" },
    };
    const c = colors[severity] || colors.info;
    const toast = document.createElement("div");
    toast.textContent = message;
    toast.style.cssText =
        `position:fixed;top:20px;right:20px;z-index:10001;padding:12px 18px 12px 15px;` +
        `border-radius:8px;font-size:13px;font-weight:500;font-family:${FONT_STACK};` +
        `background:${c.bg};border:1px solid ${c.accent}33;color:${c.text};` +
        `border-left:3px solid ${c.accent};` +
        `box-shadow:0 8px 32px rgba(0,0,0,0.3);` +
        `transform:translateX(120%);transition:transform 0.3s cubic-bezier(0.16,1,0.3,1),opacity 0.2s ease;` +
        `pointer-events:none;`;
    document.body.appendChild(toast);
    requestAnimationFrame(() => {
        toast.style.transform = "translateX(0)";
    });
    setTimeout(() => {
        toast.style.transform = "translateX(120%)";
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function createOverlay(onClose) {
    const overlay = document.createElement("div");
    overlay.style.cssText = OVERLAY_STYLE;
    overlay.addEventListener("click", (e) => {
        if (e.target === overlay) onClose();
    });
    return overlay;
}

function createDialog() {
    const dialog = document.createElement("div");
    dialog.style.cssText = DIALOG_STYLE;
    return dialog;
}

function createButton(text, style, onClick) {
    const btn = document.createElement("button");
    btn.className = "erpk-btn";
    btn.textContent = text;
    btn.style.cssText = style;
    btn.addEventListener("click", onClick);
    return btn;
}

// Lucide-style "workflow" glyph (two blocks + connector). Built via
// createElementNS so the SVG lives in the proper XML namespace and inherits
// currentColor from the row for automatic theming.
function createWorkflowIcon() {
    const SVG_NS = "http://www.w3.org/2000/svg";
    const wrap = document.createElement("div");
    wrap.style.cssText =
        "flex-shrink:0;width:28px;height:28px;display:flex;align-items:center;justify-content:center;" +
        "border-radius:6px;background:rgba(79,143,247,0.08);color:#8bb4f7;";

    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("width", "16");
    svg.setAttribute("height", "16");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "1.75");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("stroke-linejoin", "round");
    svg.setAttribute("aria-hidden", "true");

    const rect1 = document.createElementNS(SVG_NS, "rect");
    rect1.setAttribute("width", "8");
    rect1.setAttribute("height", "8");
    rect1.setAttribute("x", "3");
    rect1.setAttribute("y", "3");
    rect1.setAttribute("rx", "2");

    const path = document.createElementNS(SVG_NS, "path");
    path.setAttribute("d", "M7 11v4a2 2 0 0 0 2 2h4");

    const rect2 = document.createElementNS(SVG_NS, "rect");
    rect2.setAttribute("width", "8");
    rect2.setAttribute("height", "8");
    rect2.setAttribute("x", "13");
    rect2.setAttribute("y", "13");
    rect2.setAttribute("rx", "2");

    svg.appendChild(rect1);
    svg.appendChild(path);
    svg.appendChild(rect2);
    wrap.appendChild(svg);
    return wrap;
}

// ── Browse Dialog ────────────────────────────────────────────────

async function showBrowseDialog() {
    const overlay = createOverlay(() => overlay.remove());
    const dialog = createDialog();
    overlay.appendChild(dialog);

    // Header
    const header = document.createElement("div");
    header.style.cssText =
        "display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;";
    const title = document.createElement("h3");
    title.textContent = "Shared Workflows";
    title.style.cssText = "margin:0;color:#e8eaed;font-size:15px;font-weight:600;letter-spacing:0.01em;";
    header.appendChild(title);
    header.appendChild(
        createButton("Close", BUTTON_STYLE, () => overlay.remove())
    );
    dialog.appendChild(header);

    // List container
    const listContainer = document.createElement("div");
    listContainer.style.cssText = "overflow-y:auto;flex:1;margin:0 -4px;";
    dialog.appendChild(listContainer);

    async function refreshList() {
        clearChildren(listContainer);
        const workflows = await listSharedWorkflows();

        if (workflows.length === 0) {
            const empty = document.createElement("div");
            empty.textContent = "No shared workflows yet.";
            empty.style.cssText =
                "color:#6b6f80;text-align:center;padding:32px 0;font-size:13px;font-style:italic;";
            listContainer.appendChild(empty);
            return;
        }

        for (const wf of workflows) {
            const row = document.createElement("div");
            row.className = "erpk-row";
            row.style.cssText =
                "display:flex;align-items:center;justify-content:space-between;padding:10px 12px;" +
                "border-radius:6px;gap:12px;transition:background 0.15s ease;";

            row.appendChild(createWorkflowIcon());

            const info = document.createElement("div");
            info.style.cssText = "flex:1;min-width:0;";
            const nameEl = document.createElement("div");
            nameEl.textContent = wf.name;
            nameEl.style.cssText =
                "font-size:13px;color:#e8eaed;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;";
            const meta = document.createElement("div");
            const parts = [formatBytes(wf.size), formatDate(wf.mtime)];
            if (wf.created_by) parts.push(`by ${wf.created_by}`);
            if (wf.modified_by && wf.modified_by !== wf.created_by)
                parts.push(`edited by ${wf.modified_by}`);
            meta.textContent = parts.join("  \u00b7  ");
            meta.style.cssText = "font-size:11px;color:#6b6f80;margin-top:3px;letter-spacing:0.01em;";
            info.appendChild(nameEl);
            info.appendChild(meta);
            row.appendChild(info);

            const actions = document.createElement("div");
            actions.style.cssText = "display:flex;gap:6px;flex-shrink:0;";

            actions.appendChild(
                createButton("Load", PRIMARY_BUTTON_STYLE, async () => {
                    const data = await getSharedWorkflow(wf.name);
                    if (data) {
                        await app.loadGraphData(data, true, true, wf.name + ".json");
                        linkedSharedWorkflowName = wf.name;
                        overlay.remove();
                        showToast(`Loaded "${wf.name}"`);
                    }
                })
            );

            actions.appendChild(
                createButton("Delete", DANGER_BUTTON_STYLE, async () => {
                    if (
                        !confirm(
                            `Delete shared workflow "${wf.name}"?`
                        )
                    )
                        return;
                    const deleted = await deleteSharedWorkflow(wf.name);
                    if (deleted) showToast(`Deleted "${wf.name}"`);
                    refreshList();
                })
            );

            row.appendChild(actions);
            listContainer.appendChild(row);
        }
    }

    await refreshList();
    document.body.appendChild(overlay);
}

// ── Save Dialog ──────────────────────────────────────────────────

function showSaveDialog(onSave) {
    const overlay = createOverlay(() => overlay.remove());
    const dialog = createDialog();
    dialog.style.minWidth = "360px";
    overlay.appendChild(dialog);

    const title = document.createElement("h3");
    title.textContent = "Share Current Workflow";
    title.style.cssText = "margin:0 0 20px 0;color:#e8eaed;font-size:15px;font-weight:600;letter-spacing:0.01em;";
    dialog.appendChild(title);

    const input = document.createElement("input");
    input.type = "text";
    input.className = "erpk-input";
    input.placeholder = "Workflow name";
    input.style.cssText =
        "width:100%;padding:10px 12px;border:1px solid rgba(255,255,255,0.08);border-radius:8px;" +
        `background:rgba(255,255,255,0.04);color:#e8eaed;font-size:14px;font-family:${FONT_STACK};` +
        "box-sizing:border-box;transition:border-color 0.15s ease,box-shadow 0.15s ease;";
    dialog.appendChild(input);

    const errorEl = document.createElement("div");
    errorEl.style.cssText =
        "color:#f07070;font-size:12px;margin-top:8px;min-height:18px;";
    dialog.appendChild(errorEl);

    const buttons = document.createElement("div");
    buttons.style.cssText =
        "display:flex;justify-content:flex-end;gap:8px;margin-top:16px;";

    buttons.appendChild(
        createButton("Cancel", BUTTON_STYLE, () => overlay.remove())
    );

    const saveBtn = createButton("Save", PRIMARY_BUTTON_STYLE, async () => {
        const name = input.value.trim();
        if (!name) {
            errorEl.textContent = "Please enter a name.";
            return;
        }
        saveBtn.disabled = true;
        saveBtn.textContent = "Saving...";
        errorEl.textContent = "";

        const workflow = app.graph.serialize();
        const resp = await saveSharedWorkflow(name, workflow);
        if (resp.ok) {
            linkedSharedWorkflowName = name;
            overlay.remove();
            showToast(`Shared "${name}"`);
            if (onSave) onSave();
        } else {
            const data = await resp.json().catch(() => null);
            errorEl.textContent =
                data?.error || "Failed to save workflow.";
            saveBtn.disabled = false;
            saveBtn.textContent = "Save";
        }
    });
    buttons.appendChild(saveBtn);
    dialog.appendChild(buttons);

    input.value =
        linkedSharedWorkflowName || getActiveWorkflowName() || "";

    document.body.appendChild(overlay);
    input.focus();
}

// ── Settings Panel Workflows Section ─────────────────────────────

const SETTINGS_PANEL_ID = "erpk-shared-workflows-panel";

function createSettingsWorkflowList() {
    const section = document.createElement("div");
    section.id = SETTINGS_PANEL_ID;
    section.style.cssText =
        `margin-top:20px;padding-top:20px;font-family:${FONT_STACK};` +
        "border-top:1px solid rgba(255,255,255,0.06);";

    const header = document.createElement("div");
    header.style.cssText =
        "display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;";
    const title = document.createElement("h3");
    title.textContent = "Shared Workflows";
    title.style.cssText = "margin:0;font-size:inherit;font-weight:700;color:inherit;";
    header.appendChild(title);

    const listContainer = document.createElement("div");
    listContainer.style.cssText = "max-height:240px;overflow-y:auto;margin:0 -4px;";

    async function refreshList() {
        clearChildren(listContainer);
        const workflows = await listSharedWorkflows();

        if (workflows.length === 0) {
            const empty = document.createElement("div");
            empty.textContent = "No shared workflows yet.";
            empty.style.cssText =
                "color:#6b6f80;text-align:center;padding:20px 0;font-size:13px;font-style:italic;";
            listContainer.appendChild(empty);
            return;
        }

        for (const wf of workflows) {
            const row = document.createElement("div");
            row.className = "erpk-row";
            row.style.cssText =
                "display:flex;align-items:center;justify-content:space-between;padding:8px 10px;" +
                "border-radius:6px;gap:8px;transition:background 0.15s ease;";

            row.appendChild(createWorkflowIcon());

            const info = document.createElement("div");
            info.style.cssText = "flex:1;min-width:0;";
            const nameEl = document.createElement("div");
            nameEl.textContent = wf.name;
            nameEl.style.cssText =
                "font-size:13px;color:#e8eaed;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;";
            const meta = document.createElement("div");
            const parts = [formatBytes(wf.size), formatDate(wf.mtime)];
            if (wf.created_by) parts.push(`by ${wf.created_by}`);
            if (wf.modified_by && wf.modified_by !== wf.created_by)
                parts.push(`edited by ${wf.modified_by}`);
            meta.textContent = parts.join("  \u00b7  ");
            meta.style.cssText = "font-size:11px;color:#6b6f80;margin-top:3px;letter-spacing:0.01em;";
            info.appendChild(nameEl);
            info.appendChild(meta);
            row.appendChild(info);

            const actions = document.createElement("div");
            actions.style.cssText = "display:flex;gap:6px;flex-shrink:0;";

            actions.appendChild(
                createButton("Load", PRIMARY_BUTTON_STYLE, async () => {
                    const data = await getSharedWorkflow(wf.name);
                    if (data) {
                        await app.loadGraphData(data, true, true, wf.name + ".json");
                        linkedSharedWorkflowName = wf.name;
                        showToast(`Loaded "${wf.name}"`);
                    }
                })
            );

            actions.appendChild(
                createButton("Delete", DANGER_BUTTON_STYLE, async () => {
                    if (
                        !confirm(
                            `Delete shared workflow "${wf.name}"?`
                        )
                    )
                        return;
                    const deleted = await deleteSharedWorkflow(wf.name);
                    if (deleted) showToast(`Deleted "${wf.name}"`);
                    refreshList();
                })
            );

            row.appendChild(actions);
            listContainer.appendChild(row);
        }
    }

    header.appendChild(
        createButton("Share Current", PRIMARY_BUTTON_STYLE, () =>
            showSaveDialog(refreshList)
        )
    );
    section.appendChild(header);
    section.appendChild(listContainer);

    refreshList();
    return section;
}

function tryInjectSettingsPanel() {
    if (document.getElementById(SETTINGS_PANEL_ID)) return;

    const allText = document.querySelectorAll(
        ".p-dialog-content span, .p-dialog-content label, " +
            ".comfy-modal-content span, .comfy-modal-content label"
    );
    let firstLabel = null;
    let lastLabel = null;
    for (const el of allText) {
        const text = el.textContent.trim();
        if (text === "Anthropic API Key" && !firstLabel) firstLabel = el;
        if (text === "WaveSpeed API Key") lastLabel = el;
    }
    if (!firstLabel || !lastLabel) return;

    // Find the lowest common ancestor of first and last ERPK settings —
    // this is the settings content container, not the full dialog wrapper
    const ancestors = new Set();
    let node = firstLabel;
    while (node) {
        ancestors.add(node);
        node = node.parentElement;
    }
    let container = lastLabel;
    while (container) {
        if (ancestors.has(container)) break;
        container = container.parentElement;
    }
    if (!container) return;

    container.appendChild(createSettingsWorkflowList());
}

function observeSettingsForWorkflows() {
    const observer = new MutationObserver(() => {
        const dialogOpen =
            document.querySelector(".p-dialog-content") ||
            document.querySelector(".comfy-modal-content");
        if (dialogOpen) {
            tryInjectSettingsPanel();
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });
}

// ── Open ERPK Settings panel ─────────────────────────────────────

// Open ComfyUI's Settings dialog and navigate to the ERPK category.
// ComfyUI marks the dialog with data-testid="settings-dialog" and each sidebar
// category with a stable data-nav-id attribute (the ERPK category is
// data-nav-id="root/ERPK"). We wait for the dialog to appear, then click the
// ERPK nav item. Text-matching and search-box filtering are kept as fallbacks
// if ComfyUI renames those attributes upstream.
function openErpkSettings() {
    const btn = document.querySelector(".comfy-settings-btn");
    if (!btn) {
        console.warn("[ERPK] Could not find Comfy settings button");
        return;
    }
    btn.click();

    let attempts = 0;
    const maxAttempts = 30;

    const tryNavigate = () => {
        const dialog =
            document.querySelector("[data-testid='settings-dialog']") ||
            document.querySelector(".p-dialog-content") ||
            document.querySelector(".comfy-modal-content");
        if (!dialog) return false;

        // Strategy 1: ComfyUI's stable data-nav-id attribute on the category button
        const navItem = dialog.querySelector("[data-nav-id='root/ERPK']");
        if (navItem) {
            navItem.click();
            return true;
        }

        // Strategy 2: text-match on a nav-role element whose label is "ERPK"
        const labeled = dialog.querySelectorAll(
            "[role='button'], [aria-label], .p-treenode-label, .p-tree-node-label"
        );
        for (const el of labeled) {
            const text = (el.getAttribute("aria-label") || el.textContent || "").trim();
            if (text === "ERPK") {
                el.click();
                return true;
            }
        }

        // Strategy 3: fall back to filtering via the settings search box
        const searchInput =
            dialog.querySelector("input[placeholder*='Search' i]") ||
            document.querySelector(".settings-search-box input");
        if (searchInput) {
            const setter = Object.getOwnPropertyDescriptor(
                HTMLInputElement.prototype,
                "value"
            ).set;
            setter.call(searchInput, "ERPK");
            searchInput.dispatchEvent(new Event("input", { bubbles: true }));
            return true;
        }

        return false;
    };

    const poll = () => {
        if (tryNavigate()) return;
        if (++attempts < maxAttempts) {
            setTimeout(poll, 100);
        } else {
            console.warn(
                "[ERPK] Could not locate ERPK category or settings search " +
                "after 3s. ComfyUI settings DOM may have changed."
            );
        }
    };
    setTimeout(poll, 100);
}

// ── Extension registration ───────────────────────────────────────

app.registerExtension({
    name: "ERPK.SharedWorkflows",

    async setup() {
        const origGetCanvasMenuOptions =
            LGraphCanvas.prototype.getCanvasMenuOptions;
        LGraphCanvas.prototype.getCanvasMenuOptions = function (...args) {
            const options = origGetCanvasMenuOptions.apply(this, [...args]);
            options.push(null); // separator
            const erpkItems = [
                {
                    content: "Settings...",
                    callback: () => openErpkSettings(),
                },
                null, // separator
                {
                    content: "Browse Shared Workflows...",
                    callback: () => showBrowseDialog(),
                },
                {
                    content: "Share Current Workflow...",
                    callback: () => showSaveDialog(),
                },
            ];
            if (linkedSharedWorkflowName) {
                erpkItems.push(null); // separator
                erpkItems.push({
                    content: `Save to "${linkedSharedWorkflowName}"`,
                    callback: async () => {
                        const workflow = app.graph.serialize();
                        const resp = await saveSharedWorkflow(
                            linkedSharedWorkflowName,
                            workflow
                        );
                        if (resp.ok) {
                            showToast(`Saved to "${linkedSharedWorkflowName}"`);
                        } else {
                            showToast("Failed to save workflow", "error");
                        }
                    },
                });
            }
            options.push({
                content: "\uD83C\uDD74 ERPK",
                submenu: { options: erpkItems },
            });
            return options;
        };

        injectStylesheet();
        observeSettingsForWorkflows();
    },
});
