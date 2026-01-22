// ABOUTME: JavaScript extension for the ERPK_ConcatenateStrings node.
// ABOUTME: Provides add/remove buttons for input slots while maintaining connectability.

import { app } from "../../../scripts/app.js";

const NODE_ID = "ERPK_ConcatenateStrings";
const MAX_INPUTS = 10;
const INITIAL_INPUTS = 2;

app.registerExtension({
    name: "erpk.utils.concat_strings",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== NODE_ID) {
            return;
        }

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = async function () {
            const result = onNodeCreated?.apply(this, arguments);

            // Track active input count
            this.activeInputCount = this.properties?.activeInputCount || INITIAL_INPUTS;
            this.properties = this.properties || {};
            this.properties.activeInputCount = this.activeInputCount;

            // Delay to ensure widgets exist
            setTimeout(() => {
                this._setupUI();
            }, 50);

            return result;
        };

        // Restore state when loading workflow
        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            const result = onConfigure?.apply(this, arguments);

            if (info.properties?.activeInputCount) {
                this.activeInputCount = info.properties.activeInputCount;
            }

            setTimeout(() => {
                this._setupUI();
            }, 100);

            return result;
        };

        // Setup the UI with proper visibility and buttons
        nodeType.prototype._setupUI = function () {
            this._updateInputVisibility();
            this._ensureAddButton();
            this._resizeNode();
        };

        // Update visibility of text/label widgets and inputs
        nodeType.prototype._updateInputVisibility = function () {
            if (!this.widgets) return;

            for (const widget of this.widgets) {
                const textMatch = widget.name.match(/^text_(\d+)$/);
                const labelMatch = widget.name.match(/^label_(\d+)$/);

                if (textMatch) {
                    const idx = parseInt(textMatch[1]);
                    widget.hidden = idx > this.activeInputCount;
                } else if (labelMatch) {
                    const idx = parseInt(labelMatch[1]);
                    widget.hidden = idx > this.activeInputCount;
                }
            }

            // Hide/show corresponding input slots
            if (this.inputs) {
                for (const input of this.inputs) {
                    const textMatch = input.name.match(/^text_(\d+)$/);
                    const labelMatch = input.name.match(/^label_(\d+)$/);

                    if (textMatch) {
                        const idx = parseInt(textMatch[1]);
                        input.hidden = idx > this.activeInputCount;
                    } else if (labelMatch) {
                        const idx = parseInt(labelMatch[1]);
                        input.hidden = idx > this.activeInputCount;
                    }
                }
            }
        };

        // Ensure add button exists and is at the end
        nodeType.prototype._ensureAddButton = function () {
            if (!this.widgets) return;

            // Remove existing control buttons
            this.widgets = this.widgets.filter(w =>
                w.name !== "_add_btn" && !w.name.startsWith("_remove_")
            );

            const self = this;

            // Add remove buttons for each active input (except if only one)
            if (this.activeInputCount > 1) {
                for (let i = this.activeInputCount; i >= 1; i--) {
                    // Find the label widget for this index to insert after
                    const labelWidgetIdx = this.widgets.findIndex(w => w.name === `label_${i}`);
                    if (labelWidgetIdx >= 0) {
                        const removeBtn = {
                            type: "button",
                            name: `_remove_${i}`,
                            value: `Remove input ${i}`,
                            callback: () => {
                                self._removeInput(i);
                            },
                            options: { serialize: false },
                            hidden: false,
                        };
                        // Insert after the label widget
                        this.widgets.splice(labelWidgetIdx + 1, 0, removeBtn);
                    }
                }
            }

            // Add "Add Input" button at the end if not at max
            if (this.activeInputCount < MAX_INPUTS) {
                this.addWidget(
                    "button",
                    "_add_btn",
                    "+ Add Input",
                    () => {
                        self._addInput();
                    },
                    { serialize: false }
                );
            }
        };

        // Add a new input slot
        nodeType.prototype._addInput = function () {
            if (this.activeInputCount < MAX_INPUTS) {
                this.activeInputCount++;
                this.properties.activeInputCount = this.activeInputCount;
                this._setupUI();
            }
        };

        // Remove an input slot
        nodeType.prototype._removeInput = function (index) {
            if (this.activeInputCount <= 1) return;

            // Clear the values of the removed input
            const textWidget = this.widgets.find(w => w.name === `text_${index}`);
            const labelWidget = this.widgets.find(w => w.name === `label_${index}`);
            if (textWidget) textWidget.value = "";
            if (labelWidget) labelWidget.value = "";

            // Disconnect any links to this input
            if (this.inputs) {
                const textInput = this.inputs.find(inp => inp.name === `text_${index}`);
                const labelInput = this.inputs.find(inp => inp.name === `label_${index}`);
                if (textInput && textInput.link != null) {
                    app.graph.removeLink(textInput.link);
                }
                if (labelInput && labelInput.link != null) {
                    app.graph.removeLink(labelInput.link);
                }
            }

            // Shift values up from higher indices
            for (let i = index; i < this.activeInputCount; i++) {
                const nextText = this.widgets.find(w => w.name === `text_${i + 1}`);
                const nextLabel = this.widgets.find(w => w.name === `label_${i + 1}`);
                const currText = this.widgets.find(w => w.name === `text_${i}`);
                const currLabel = this.widgets.find(w => w.name === `label_${i}`);

                if (currText && nextText) currText.value = nextText.value;
                if (currLabel && nextLabel) currLabel.value = nextLabel.value;
            }

            // Clear the last slot
            const lastText = this.widgets.find(w => w.name === `text_${this.activeInputCount}`);
            const lastLabel = this.widgets.find(w => w.name === `label_${this.activeInputCount}`);
            if (lastText) lastText.value = "";
            if (lastLabel) lastLabel.value = "";

            this.activeInputCount--;
            this.properties.activeInputCount = this.activeInputCount;
            this._setupUI();
        };

        // Resize node to fit content
        nodeType.prototype._resizeNode = function () {
            const sz = this.computeSize();
            this.setSize([Math.max(sz[0], 300), sz[1]]);
            this.setDirtyCanvas(true, true);
        };

        return nodeType;
    },
});
