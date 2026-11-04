// ABOUTME: ComfyUI extension entry for the Image Grid Loader node's drop-and-reorder image grid.
// ABOUTME: Mounts the grid as a DOM widget, uploads files to input/, and draws the count in the title bar.
// @ts-check

// app.js and api.js are resolved by ComfyUI at runtime; they are not present at type-check time.
// @ts-ignore
import { app } from "../../../scripts/app.js";
// @ts-ignore
import { api } from "../../../scripts/api.js";

import { storedName, viewPath } from "./image_grid/grid_list.js";
import { MIN_NODE_WIDTH, TITLE_COUNT_COLOR, TITLE_COUNT_FULL_COLOR } from "./image_grid/styles.js";
import { createImageGrid } from "./image_grid/widget.js";

const NODE_ID = "ImageGridLoader";

/** @param {File} file */
async function uploadToInput(file) {
    const body = new FormData();
    body.append("image", file);
    body.append("type", "input");
    const response = await api.fetchApi("/upload/image", { method: "POST", body });
    if (response.status !== 200) {
        throw new Error(`Upload of "${file.name}" failed: ${response.status} ${response.statusText}.`);
    }
    // The route renames on a name clash and reuses an identical file, so the
    // answered name, not the local one, is what lands in the list.
    return storedName(await response.json());
}

const gridIO = {
    upload: uploadToInput,
    imageUrl: (/** @type {string} */ stored) => api.apiURL(viewPath(stored)),
};

app.registerExtension({
    name: "erpk.imageGridLoader",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData?.name !== NODE_ID) return;

        const origComputeSize = nodeType.prototype.computeSize;
        nodeType.prototype.computeSize = function () {
            const size = origComputeSize?.apply(this, arguments) ?? [MIN_NODE_WIDTH, 0];
            return [Math.max(size[0], MIN_NODE_WIDTH), size[1]];
        };

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = onNodeCreated?.apply(this, arguments);
            const grid = createImageGrid(this, gridIO);
            this._erpkImageGrid = grid;
            this.addDOMWidget("image_grid", "erpk_image_grid", grid.root, {
                serialize: false,
                hideOnZoom: false,
                getMinHeight: () => grid.desiredHeight(),
                getMaxHeight: () => grid.desiredHeight(),
            });
            const computed = this.computeSize();
            if (this.size[0] < computed[0]) this.size[0] = computed[0];
            if (this.size[1] < computed[1]) this.size[1] = computed[1];
            grid.layout();
            // Same deferral as the region editor: widgets can still be
            // materializing when the node is created. A fresh node holds "[]".
            setTimeout(() => grid.setup(), 50);
            return r;
        };

        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function () {
            const r = onConfigure?.apply(this, arguments);
            const grid = this._erpkImageGrid;
            if (grid) {
                // widgets_values are assigned by now; rebuild before anything can queue.
                grid.setup();
                grid.loadFromWidget();
            }
            return r;
        };

        const onResize = nodeType.prototype.onResize;
        nodeType.prototype.onResize = function () {
            const r = onResize?.apply(this, arguments);
            this._erpkImageGrid?.layout();
            return r;
        };

        // Files dropped on the title bar reach the canvas, not the grid; take
        // them here so they join the grid instead of loading as a workflow.
        const onDragOver = nodeType.prototype.onDragOver;
        nodeType.prototype.onDragOver = function (e) {
            return e?.dataTransfer?.types?.includes("Files") || (onDragOver?.apply(this, arguments) ?? false);
        };
        const onDragDrop = nodeType.prototype.onDragDrop;
        nodeType.prototype.onDragDrop = function (e) {
            const files = [...(e?.dataTransfer?.files ?? [])];
            if (!this._erpkImageGrid || files.length === 0) return onDragDrop?.apply(this, arguments) ?? false;
            this._erpkImageGrid.addFiles(files);
            return true;
        };

        const onDrawForeground = nodeType.prototype.onDrawForeground;
        nodeType.prototype.onDrawForeground = function (ctx) {
            const r = onDrawForeground?.apply(this, arguments);
            const count = this._erpkImageGrid?.titleCount();
            if (!count || this.flags?.collapsed) return r;
            const { text, overCap } = count;
            const titleHeight = /** @type {any} */ (globalThis).LiteGraph?.NODE_TITLE_HEIGHT ?? 30;
            ctx.save();
            ctx.font = "500 12px 'Segoe UI', system-ui, sans-serif";
            ctx.textAlign = "right";
            ctx.textBaseline = "middle";
            ctx.fillStyle = overCap ? TITLE_COUNT_FULL_COLOR : TITLE_COUNT_COLOR;
            ctx.fillText(text, this.size[0] - 10, -titleHeight / 2);
            ctx.restore();
            return r;
        };
    },
});
