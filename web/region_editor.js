// ABOUTME: ComfyUI extension entry for the RegionalPromptBuilder canvas region editor.
// ABOUTME: Registers the node hooks and mounts the editor module tree (web/regions/) on each node.
// @ts-check

// app.js is resolved by ComfyUI at runtime; it is not present at type-check time.
// @ts-ignore
import { app } from "../../../scripts/app.js";

import { createRegionEditor } from "./regions/editor.js";
import { NODE_ID, MIN_NODE_WIDTH } from "./regions/constants.js";
import {
    desiredEditorHeight,
    pinRootWidth,
    repairManagedWidgetValues,
} from "./regions/node_access.js";

app.registerExtension({
    name: "erpk.regionEditor",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData?.name !== NODE_ID) return;

        // The editor's height reaches the layout through the DOM widget's
        // getMinHeight/getMaxHeight (computeSize folds widget layout sizes in
        // by itself), so the node override only floors the width.
        const origComputeSize = nodeType.prototype.computeSize;
        nodeType.prototype.computeSize = function () {
            const size = origComputeSize?.apply(this, arguments) ?? [MIN_NODE_WIDTH, 0];
            return [Math.max(size[0], MIN_NODE_WIDTH), size[1]];
        };

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = onNodeCreated?.apply(this, arguments);

            const editor = createRegionEditor(this);
            this._erpkRegionEditor = editor;

            this.addDOMWidget("region_editor", "erpk_region_editor", editor.root, {
                serialize: false,
                hideOnZoom: false,
                // Pinning min == max keeps the canvas aspect-true at the node's
                // width. The scene-prompt field is capped to a fixed height
                // (editor.js capPromptHeight), so the node sizes to its content
                // rather than letting the prompt balloon to fill it.
                getMinHeight: () => desiredEditorHeight(this),
                getMaxHeight: () => desiredEditorHeight(this),
            });

            const computed = this.computeSize();
            if (this.size[0] < computed[0]) this.size[0] = computed[0];
            if (this.size[1] < computed[1]) this.size[1] = computed[1];
            pinRootWidth(this);

            // Widgets (including regions_data) can finish materializing after
            // creation; defer the lookup-dependent setup until they exist.
            setTimeout(() => {
                editor.setup();
                editor.loadFromWidget();
                editor.layout();
            }, 50);

            return r;
        };

        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            const r = onConfigure?.apply(this, arguments);
            // The restore can leave removal_fill/chroma_color holding a value the
            // node no longer accepts; settle them before anything can queue.
            repairManagedWidgetValues(this);
            const editor = this._erpkRegionEditor;
            if (editor) {
                // Widget values from the workflow JSON land during configure;
                // re-read them once the restore has settled.
                setTimeout(() => {
                    editor.setup();
                    editor.loadFromWidget();
                    pinRootWidth(this);
                    editor.layout();
                }, 50);
            }
            return r;
        };

        const origOnResize = nodeType.prototype.onResize;
        nodeType.prototype.onResize = function (size) {
            const r = origOnResize?.apply(this, arguments);
            pinRootWidth(this);
            this._erpkRegionEditor?.layout();
            return r;
        };

        // Repaint when the reference image link is attached or removed.
        const origOnConnectionsChange = nodeType.prototype.onConnectionsChange;
        nodeType.prototype.onConnectionsChange = function () {
            const r = origOnConnectionsChange?.apply(this, arguments);
            this._erpkRegionEditor?.layout();
            return r;
        };

        const onRemoved = nodeType.prototype.onRemoved;
        nodeType.prototype.onRemoved = function () {
            this._erpkRegionEditor?.destroy();
            this._erpkRegionEditor = null;
            return onRemoved?.apply(this, arguments);
        };
    },
});
