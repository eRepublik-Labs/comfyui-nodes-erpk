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

// ── Shared styles ────────────────────────────────────────────────

const OVERLAY_STYLE =
    "position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.6);" +
    "display:flex;align-items:center;justify-content:center;z-index:10000;";

const DIALOG_STYLE =
    "background:#1e1e1e;color:#ccc;border:1px solid #444;border-radius:8px;" +
    "padding:24px;min-width:420px;max-width:640px;max-height:80vh;" +
    "display:flex;flex-direction:column;font-family:sans-serif;";

const BUTTON_STYLE =
    "padding:6px 14px;border:1px solid #555;border-radius:4px;" +
    "background:#2a2a2a;color:#ccc;cursor:pointer;font-size:13px;";

const PRIMARY_BUTTON_STYLE =
    BUTTON_STYLE.replace("background:#2a2a2a", "background:#2563eb").replace(
        "color:#ccc",
        "color:#fff"
    );

const DANGER_BUTTON_STYLE =
    BUTTON_STYLE.replace("background:#2a2a2a", "background:#7f1d1d").replace(
        "color:#ccc",
        "color:#fca5a5"
    );

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
        success: { bg: "#14532d", border: "#22c55e", text: "#bbf7d0" },
        error: { bg: "#7f1d1d", border: "#ef4444", text: "#fca5a5" },
        info: { bg: "#1e3a5f", border: "#3b82f6", text: "#bfdbfe" },
    };
    const c = colors[severity] || colors.info;
    const toast = document.createElement("div");
    toast.textContent = message;
    toast.style.cssText =
        `position:fixed;top:20px;right:20px;z-index:10001;padding:10px 18px;` +
        `border-radius:6px;font-size:13px;font-family:sans-serif;` +
        `background:${c.bg};border:1px solid ${c.border};color:${c.text};` +
        `opacity:0;transition:opacity 0.3s ease;pointer-events:none;`;
    document.body.appendChild(toast);
    requestAnimationFrame(() => {
        toast.style.opacity = "1";
    });
    setTimeout(() => {
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
    btn.textContent = text;
    btn.style.cssText = style;
    btn.addEventListener("click", onClick);
    return btn;
}

// ── Browse Dialog ────────────────────────────────────────────────

async function showBrowseDialog() {
    const overlay = createOverlay(() => overlay.remove());
    const dialog = createDialog();
    overlay.appendChild(dialog);

    // Header
    const header = document.createElement("div");
    header.style.cssText =
        "display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;";
    const title = document.createElement("h3");
    title.textContent = "Shared Workflows";
    title.style.cssText = "margin:0;color:#eee;font-size:16px;";
    header.appendChild(title);
    header.appendChild(
        createButton("Close", BUTTON_STYLE, () => overlay.remove())
    );
    dialog.appendChild(header);

    // List container
    const listContainer = document.createElement("div");
    listContainer.style.cssText = "overflow-y:auto;flex:1;";
    dialog.appendChild(listContainer);

    async function refreshList() {
        clearChildren(listContainer);
        const workflows = await listSharedWorkflows();

        if (workflows.length === 0) {
            const empty = document.createElement("div");
            empty.textContent = "No shared workflows yet.";
            empty.style.cssText =
                "color:#888;text-align:center;padding:32px 0;font-size:14px;";
            listContainer.appendChild(empty);
            return;
        }

        for (const wf of workflows) {
            const row = document.createElement("div");
            row.style.cssText =
                "display:flex;align-items:center;justify-content:space-between;padding:8px 12px;" +
                "border-bottom:1px solid #333;gap:12px;";

            const info = document.createElement("div");
            info.style.cssText = "flex:1;min-width:0;";
            const nameEl = document.createElement("div");
            nameEl.textContent = wf.name;
            nameEl.style.cssText =
                "font-size:14px;color:#eee;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;";
            const meta = document.createElement("div");
            const parts = [formatBytes(wf.size), formatDate(wf.mtime)];
            if (wf.created_by) parts.push(`by ${wf.created_by}`);
            if (wf.modified_by && wf.modified_by !== wf.created_by)
                parts.push(`edited by ${wf.modified_by}`);
            meta.textContent = parts.join("  |  ");
            meta.style.cssText = "font-size:11px;color:#888;margin-top:2px;";
            info.appendChild(nameEl);
            info.appendChild(meta);
            row.appendChild(info);

            const actions = document.createElement("div");
            actions.style.cssText = "display:flex;gap:6px;flex-shrink:0;";

            actions.appendChild(
                createButton("Load", PRIMARY_BUTTON_STYLE, async () => {
                    if (
                        !confirm(
                            "This will replace your current workflow. Continue?"
                        )
                    )
                        return;
                    const data = await getSharedWorkflow(wf.name);
                    if (data) {
                        await app.loadGraphData(data);
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

function showSaveDialog() {
    const overlay = createOverlay(() => overlay.remove());
    const dialog = createDialog();
    dialog.style.minWidth = "360px";
    overlay.appendChild(dialog);

    const title = document.createElement("h3");
    title.textContent = "Share Current Workflow";
    title.style.cssText = "margin:0 0 16px 0;color:#eee;font-size:16px;";
    dialog.appendChild(title);

    const input = document.createElement("input");
    input.type = "text";
    input.placeholder = "Workflow name";
    input.style.cssText =
        "width:100%;padding:8px 10px;border:1px solid #555;border-radius:4px;" +
        "background:#2a2a2a;color:#eee;font-size:14px;box-sizing:border-box;";
    dialog.appendChild(input);

    const errorEl = document.createElement("div");
    errorEl.style.cssText =
        "color:#f87171;font-size:12px;margin-top:6px;min-height:18px;";
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

// ── Open ERPK Settings panel ─────────────────────────────────────

function openErpkSettings() {
    const btn = document.querySelector(".comfy-settings-btn");
    if (!btn) return;
    btn.click();
    let attempts = 0;
    const searchERPK = () => {
        const input = document.querySelector(".settings-search-box input");
        if (input) {
            const setter = Object.getOwnPropertyDescriptor(
                HTMLInputElement.prototype,
                "value"
            ).set;
            setter.call(input, "ERPK");
            input.dispatchEvent(new Event("input", { bubbles: true }));
            return;
        }
        if (++attempts < 10) {
            setTimeout(searchERPK, 100);
        }
    };
    setTimeout(searchERPK, 100);
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
    },
});
