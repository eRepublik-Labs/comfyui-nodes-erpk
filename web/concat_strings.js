// ABOUTME: JavaScript extension for the ERPK_ConcatenateStrings node.
// ABOUTME: Manages visibility of unused text/label input slots for cleaner UI.

import { app } from "../../../scripts/app.js";

const NODE_ID = "ERPK_ConcatenateStrings";
const MAX_INPUTS = 10;
const INITIAL_VISIBLE = 3;

app.registerExtension({
    name: "erpk.utils.concat_strings",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== NODE_ID) {
            return;
        }

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = async function () {
            const result = onNodeCreated?.apply(this, arguments);

            // Track how many input slots are visible
            this.visibleInputCount = this.properties?.visibleInputCount || INITIAL_VISIBLE;
            this.properties = this.properties || {};
            this.properties.visibleInputCount = this.visibleInputCount;

            this._updateInputVisibility();
            this._addExpandButton();

            return result;
        };

        // Restore state when loading workflow
        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            const result = onConfigure?.apply(this, arguments);

            if (info.properties?.visibleInputCount) {
                this.visibleInputCount = info.properties.visibleInputCount;
            }

            // Delay to ensure widgets are created
            setTimeout(() => {
                this._updateInputVisibility();
                this._addExpandButton();
            }, 100);

            return result;
        };

        // Update visibility of text/label widgets based on visibleInputCount
        nodeType.prototype._updateInputVisibility = function () {
            if (!this.widgets) return;

            for (const widget of this.widgets) {
                // Match text_N and label_N widgets
                const textMatch = widget.name.match(/^text_(\d+)$/);
                const labelMatch = widget.name.match(/^label_(\d+)$/);

                if (textMatch) {
                    const idx = parseInt(textMatch[1]);
                    widget.hidden = idx > this.visibleInputCount;
                } else if (labelMatch) {
                    const idx = parseInt(labelMatch[1]);
                    widget.hidden = idx > this.visibleInputCount;
                }
            }

            // Also hide/show corresponding inputs
            if (this.inputs) {
                for (const input of this.inputs) {
                    const textMatch = input.name.match(/^text_(\d+)$/);
                    const labelMatch = input.name.match(/^label_(\d+)$/);

                    if (textMatch) {
                        const idx = parseInt(textMatch[1]);
                        input.hidden = idx > this.visibleInputCount;
                    } else if (labelMatch) {
                        const idx = parseInt(labelMatch[1]);
                        input.hidden = idx > this.visibleInputCount;
                    }
                }
            }

            // Update expand button text
            this._updateExpandButton();

            // Resize node
            this.setDirtyCanvas(true, true);
        };

        // Add or update expand/collapse button
        nodeType.prototype._addExpandButton = function () {
            // Remove existing button if present
            if (this.widgets) {
                const existingIdx = this.widgets.findIndex(w => w.name === "_expand_btn");
                if (existingIdx >= 0) {
                    this.widgets.splice(existingIdx, 1);
                }
            }

            const self = this;
            this.addWidget(
                "button",
                "_expand_btn",
                this._getExpandButtonText(),
                () => {
                    if (self.visibleInputCount < MAX_INPUTS) {
                        self.visibleInputCount = Math.min(self.visibleInputCount + 3, MAX_INPUTS);
                    } else {
                        self.visibleInputCount = INITIAL_VISIBLE;
                    }
                    self.properties.visibleInputCount = self.visibleInputCount;
                    self._updateInputVisibility();
                },
                { serialize: false }
            );
        };

        nodeType.prototype._getExpandButtonText = function () {
            if (this.visibleInputCount >= MAX_INPUTS) {
                return "Collapse inputs";
            }
            return `Show more inputs (${this.visibleInputCount}/${MAX_INPUTS})`;
        };

        nodeType.prototype._updateExpandButton = function () {
            if (!this.widgets) return;
            const btn = this.widgets.find(w => w.name === "_expand_btn");
            if (btn) {
                btn.value = this._getExpandButtonText();
            }
        };

        return nodeType;
    },
});
