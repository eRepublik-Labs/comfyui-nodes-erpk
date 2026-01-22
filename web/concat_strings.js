// ABOUTME: JavaScript extension for the ERPK_ConcatenateStrings node.
// ABOUTME: Provides add/remove buttons for input slots while maintaining connectability.

import { app } from "../../../scripts/app.js";

const NODE_ID = "ERPK_ConcatenateStrings";
const MAX_INPUTS = 10;
const INITIAL_INPUTS = 2;

// Create a labeled separator widget (line with centered text)
function createLabeledSeparator(node, label, markerProp) {
    const widget = node.addWidget("text", " ", "", null, { serialize: false });
    widget.disabled = true;
    widget.computeSize = () => [0, 24];
    widget[markerProp] = true;

    widget.draw = function (ctx, node, widgetWidth, y, widgetHeight) {
        const lineColor = "#666";
        const textColor = "#aaa";
        const fontSize = 11;
        const padding = 10;

        ctx.save();
        ctx.font = `${fontSize}px Arial`;
        const textWidth = ctx.measureText(label).width;
        const textX = (widgetWidth - textWidth) / 2;
        const lineY = y + widgetHeight / 2;

        // Left line
        ctx.strokeStyle = lineColor;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padding, lineY);
        ctx.lineTo(textX - 8, lineY);
        ctx.stroke();

        // Right line
        ctx.beginPath();
        ctx.moveTo(textX + textWidth + 8, lineY);
        ctx.lineTo(widgetWidth - padding, lineY);
        ctx.stroke();

        // Center text
        ctx.fillStyle = textColor;
        ctx.fillText(label, textX, y + widgetHeight / 2 + fontSize / 3);
        ctx.restore();
    };

    return widget;
}

// Create a simple line separator (no text)
function createLineSeparator(node) {
    const widget = node.addWidget("text", " ", "", null, { serialize: false });
    widget.disabled = true;
    widget.computeSize = () => [0, 16];

    widget.draw = function (ctx, node, widgetWidth, y, widgetHeight) {
        const lineColor = "#555";
        const padding = 20;
        const lineY = y + widgetHeight / 2;

        ctx.save();
        ctx.strokeStyle = lineColor;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padding, lineY);
        ctx.lineTo(widgetWidth - padding, lineY);
        ctx.stroke();
        ctx.restore();
    };

    return widget;
}

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

            // Reset stored inputs on configure
            this._allInputs = null;

            setTimeout(() => {
                this._setupUI();
            }, 100);

            return result;
        };

        // Setup the UI with proper visibility and buttons
        nodeType.prototype._setupUI = function () {
            this._removeControlWidgets();
            this._updateInputVisibility();
            this._addControlWidgets();
            this._reorderWidgets();
            this._resizeNode();
        };

        // Remove all control widgets (buttons and spacers)
        nodeType.prototype._removeControlWidgets = function () {
            if (!this.widgets) return;
            this.widgets = this.widgets.filter(w => {
                if (w.name === "\u2795 Add Input") return false;
                if (w._inputIndex !== undefined) return false; // Remove buttons
                if (w._spacerIndex !== undefined) return false; // Spacers
                if (w._isAddSpacer) return false; // Spacer before add button
                if (w._isHeaderSpacer) return false; // Spacer before first input
                return true;
            });
        };

        // Update visibility of text/label widgets and inputs
        nodeType.prototype._updateInputVisibility = function () {
            if (!this.widgets) return;

            for (const widget of this.widgets) {
                const textMatch = widget.name.match(/^Text (\d+)$/);
                const labelMatch = widget.name.match(/^Label (\d+)$/);

                if (textMatch) {
                    const idx = parseInt(textMatch[1]);
                    widget.hidden = idx > this.activeInputCount;
                } else if (labelMatch) {
                    const idx = parseInt(labelMatch[1]);
                    widget.hidden = idx > this.activeInputCount;
                }
            }

            // Store original inputs if not already stored
            if (!this._allInputs && this.inputs) {
                this._allInputs = [...this.inputs];
            }

            // Filter inputs to only show active ones
            if (this._allInputs) {
                this.inputs = this._allInputs.filter(input => {
                    const textMatch = input.name.match(/^Text (\d+)$/);
                    const labelMatch = input.name.match(/^Label (\d+)$/);

                    if (textMatch) {
                        return parseInt(textMatch[1]) <= this.activeInputCount;
                    } else if (labelMatch) {
                        return parseInt(labelMatch[1]) <= this.activeInputCount;
                    }
                    return true; // Keep delimiter, include_labels, label_on_same_line
                });
            }
        };

        // Add control widgets (buttons and spacers)
        nodeType.prototype._addControlWidgets = function () {
            if (!this.widgets) return;
            const self = this;

            // Labeled separator between config options and first input group
            const headerSep = createLabeledSeparator(this, "Inputs", "_isHeaderSpacer");

            // Add remove button and separator for each active input (if more than 1)
            if (this.activeInputCount > 1) {
                for (let i = 1; i <= this.activeInputCount; i++) {
                    const idx = i; // Capture for closure

                    // Remove button
                    const btn = this.addWidget(
                        "button",
                        "\u{1F5D1} Remove",
                        null,
                        () => {
                            self._removeInput(idx);
                        },
                        { serialize: false }
                    );
                    btn._inputIndex = idx;

                    // Line separator after each group (except the last one)
                    if (i < this.activeInputCount) {
                        const sep = createLineSeparator(this);
                        sep._spacerIndex = idx;
                    }
                }
            }

            // Spacer before add button
            const addSpacer = this.addWidget(
                "text",
                " ",
                "",
                null,
                { serialize: false }
            );
            addSpacer.disabled = true;
            addSpacer.computeSize = () => [0, 10];
            addSpacer._isAddSpacer = true;

            // Add "Add Input" button if not at max
            if (this.activeInputCount < MAX_INPUTS) {
                this.addWidget(
                    "button",
                    "\u2795 Add Input",
                    null,
                    () => {
                        self._addInput();
                    },
                    { serialize: false }
                );
            }
        };

        // Reorder widgets so remove buttons and spacers appear after their text
        nodeType.prototype._reorderWidgets = function () {
            if (!this.widgets) return;

            const newOrder = [];
            const removeButtons = [];
            const spacers = [];
            const addButton = this.widgets.find(w => w.name === "\u2795 Add Input");
            const headerSpacer = this.widgets.find(w => w._isHeaderSpacer);
            const addSpacer = this.widgets.find(w => w._isAddSpacer);

            // Separate control widgets
            for (const w of this.widgets) {
                if (w._inputIndex !== undefined) {
                    removeButtons.push(w);
                } else if (w._spacerIndex !== undefined) {
                    spacers.push(w);
                } else if (w.name !== "\u2795 Add Input" && !w._isHeaderSpacer && !w._isAddSpacer) {
                    newOrder.push(w);
                }
            }

            // Insert header spacer before first Label widget
            if (headerSpacer) {
                const label1Idx = newOrder.findIndex(w => w.name === "Label 1");
                if (label1Idx >= 0) {
                    newOrder.splice(label1Idx, 0, headerSpacer);
                }
            }

            // Insert remove buttons after their corresponding text widgets
            for (const removeBtn of removeButtons) {
                const idx = removeBtn._inputIndex;
                const textIdx = newOrder.findIndex(w => w.name === `Text ${idx}`);
                if (textIdx >= 0) {
                    newOrder.splice(textIdx + 1, 0, removeBtn);
                } else {
                    newOrder.push(removeBtn);
                }
            }

            // Insert spacers after their corresponding remove buttons
            for (const spacer of spacers) {
                const idx = spacer._spacerIndex;
                // Find the remove button for this index
                const removeBtnIdx = newOrder.findIndex(w => w._inputIndex === idx);
                if (removeBtnIdx >= 0) {
                    newOrder.splice(removeBtnIdx + 1, 0, spacer);
                }
            }

            // Add add spacer and add button at the end
            if (addSpacer) {
                newOrder.push(addSpacer);
            }
            if (addButton) {
                newOrder.push(addButton);
            }

            this.widgets = newOrder;
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
            const textWidget = this.widgets.find(w => w.name === `Text ${index}`);
            const labelWidget = this.widgets.find(w => w.name === `Label ${index}`);
            if (textWidget) textWidget.value = "";
            if (labelWidget) labelWidget.value = "";

            // Disconnect any links to this input
            if (this.inputs) {
                const textInput = this.inputs.find(inp => inp.name === `Text ${index}`);
                const labelInput = this.inputs.find(inp => inp.name === `Label ${index}`);
                if (textInput && textInput.link != null) {
                    app.graph.removeLink(textInput.link);
                }
                if (labelInput && labelInput.link != null) {
                    app.graph.removeLink(labelInput.link);
                }
            }

            // Shift values up from higher indices
            for (let i = index; i < this.activeInputCount; i++) {
                const nextText = this.widgets.find(w => w.name === `Text ${i + 1}`);
                const nextLabel = this.widgets.find(w => w.name === `Label ${i + 1}`);
                const currText = this.widgets.find(w => w.name === `Text ${i}`);
                const currLabel = this.widgets.find(w => w.name === `Label ${i}`);

                if (currText && nextText) currText.value = nextText.value;
                if (currLabel && nextLabel) currLabel.value = nextLabel.value;
            }

            // Clear the last slot
            const lastText = this.widgets.find(w => w.name === `Text ${this.activeInputCount}`);
            const lastLabel = this.widgets.find(w => w.name === `Label ${this.activeInputCount}`);
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
