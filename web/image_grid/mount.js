// ABOUTME: Installs the image grid on a node type: mounts the DOM widget after the Python widgets,
// ABOUTME: rebuilds it on load, tracks the image socket that overrides it, and handles the title bar.
// @ts-check

import { MIN_NODE_WIDTH, TITLE_COUNT_COLOR, TITLE_COUNT_FULL_COLOR } from "./styles.js";
import { createImageGrid } from "./widget.js";

/**
 * The node type must declare the `grid_images` widget (utils/image_grid.py
 * grid_input); the grid finds it by name.
 * @param {any} nodeType
 * @param {import("./widget.js").GridIO} io
 * @param {{ socket?: string, caps: import("./grid_list.js").GridCaps, nodeName: string }} options
 *   `socket` names the input that, when linked, the node sends instead of the grid; `caps` is
 *   the node's entry from /erpk/grid_caps; `nodeName` is what an over-cap notice names when the
 *   node has no model choice.
 */
export function installImageGrid(nodeType, io, { socket, caps, nodeName }) {
    const origComputeSize = nodeType.prototype.computeSize;
    nodeType.prototype.computeSize = function () {
        const size = origComputeSize?.apply(this, arguments) ?? [MIN_NODE_WIDTH, 0];
        return [Math.max(size[0], MIN_NODE_WIDTH), size[1]];
    };

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
        const r = onNodeCreated?.apply(this, arguments);
        const grid = createImageGrid(this, io, caps, nodeName);
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
            grid.setCollapsed(this.properties?.erpkGridCollapsed === true);
            grid.loadFromWidget();
            if (socket) grid.setSocketLinked(isSocketLinked(this, socket));
        }
        return r;
    };

    if (socket) {
        // While a node loads, LiteGraph reports every input as connected, linked
        // or not, so read the socket's link rather than trusting the arguments.
        const onConnectionsChange = nodeType.prototype.onConnectionsChange;
        nodeType.prototype.onConnectionsChange = function () {
            const r = onConnectionsChange?.apply(this, arguments);
            this._erpkImageGrid?.setSocketLinked(isSocketLinked(this, socket));
            return r;
        };
    }

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
}

/** @param {any} node @param {string} socket */
function isSocketLinked(node, socket) {
    const slot = node.findInputSlot(socket);
    if (slot === -1) throw new Error(`${node.type} node ${node.id} has no "${socket}" input`);
    return node.isInputConnected(slot);
}
